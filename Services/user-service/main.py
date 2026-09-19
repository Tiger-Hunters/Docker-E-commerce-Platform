from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pathlib import Path
from sqlalchemy.engine import URL
import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- Authentication Configuration ---
def read_secret(file_env: str, fallback_env: str | None = None) -> str:
    secret_file = os.getenv(file_env)
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()

    # Local-development fallback only
    if fallback_env:
        return os.getenv(fallback_env, "secret")

    raise RuntimeError(f"Missing required secret: {file_env}")
# JWT_SECRET = os.getenv("JWT_SECRET")
JWT_SECRET = read_secret("JWT_SECRET_FILE")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60

# --- Password Hashing ---
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        600_000
    ).hex()

    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    # New secure password format
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, salt, expected_hash = stored_password.split("$")
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt),
                600_000
            ).hex()

            return hmac.compare_digest(actual_hash, expected_hash)
        except (ValueError, TypeError):
            return False

    # Legacy format used by existing accounts
    return hmac.compare_digest(
        stored_password,
        password + "_hashed"
    )

# --- Database Setup ---
DB_USER = os.getenv("DB_USER", "ecom_user")
DB_HOST = os.getenv("DB_HOST", "localhost")



DB_PASSWORD = read_secret("DB_PASSWORD_FILE", "DB_PASSWORD")

DATABASE_URL = URL.create(
    drivername="postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database="user_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    passwordHash = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# --- JWT Authentication ---
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

        return user_id

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# --- Pydantic Models ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

# --- API Routes ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    new_user = UserDB(
        name=user.name,
        email=user.email,
        passwordHash=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int,current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to access this profile")

    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/api/users/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    db_user = (db.query(UserDB).filter(UserDB.email == credentials.email).first())
    if not db_user or not verify_password(credentials.password,db_user.passwordHash):
        raise HTTPException(status_code=401,detail="Invalid email or password")

    # Upgrade legacy password storage after successful login
    if not db_user.passwordHash.startswith("pbkdf2_sha256$"):
        db_user.passwordHash = hash_password(credentials.password)
        db.commit()

    # Generate signed JWT
    now = datetime.now(timezone.utc)
    payload = {"sub": str(db_user.id),"iat": now,"exp": now + timedelta(minutes=JWT_EXPIRATION_MINUTES)}
    token = jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGORITHM)
    return {"token": token,"user": db_user}
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)