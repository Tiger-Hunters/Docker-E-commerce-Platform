from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn
import redis
import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from pathlib import Path
from sqlalchemy.engine import URL
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# --- Database Setup ---
DB_USER = os.getenv("DB_USER", "ecom_user")
DB_HOST = os.getenv("DB_HOST", "localhost")

def read_secret(file_env: str, fallback_env: str | None = None) -> str:
    secret_file = os.getenv(file_env)
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()

    # Local-development fallback only
    if fallback_env:
        return os.getenv(fallback_env, "secret")

    raise RuntimeError(f"Missing required secret: {file_env}")

DB_PASSWORD = read_secret("DB_PASSWORD_FILE", "DB_PASSWORD")

DATABASE_URL = URL.create(
    drivername="postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database="product_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stockQuantity = Column(Integer, nullable=False)
    category = Column(String)
    isActive = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Redis Setup (Hardened for Docker Drops) ---

# --- Redis Setup ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = read_secret("REDIS_PASSWORD_FILE", "REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    password=REDIS_PASSWORD,
    db=0,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    health_check_interval=2,
)

app = FastAPI()
# --- JWT Authentication ---
def read_jwt_secret() -> str:
    secret_file = os.getenv("JWT_SECRET_FILE")
    if not secret_file:
        raise RuntimeError("JWT_SECRET_FILE is required")
    return Path(secret_file).read_text(encoding="utf-8").strip()


JWT_SECRET = read_jwt_secret()
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> int:
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
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stockQuantity: int
    category: str

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    price: float
    stockQuantity: int
    category: str
    isActive: bool

# --- API Routes ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate,current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    new_product = ProductDB(**product.model_dump(), isActive=True)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/api/products", response_model=list[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(ProductDB).filter(ProductDB.isActive == True).all()

@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{product_id}"
    redis_available = True
    
    # 1. FAULT-TOLERANT CACHE HIT
    try:
        cached = redis_client.get(cache_key)
        if cached:
            print(f"REDIS HIT for product {product_id}!", flush=True)
            return json.loads(cached)
    except Exception as e:
        print(f"REDIS ERROR: {e}. Bypassing cache...", flush=True)
        redis_available = False # Mini Circuit-Breaker: Mark Redis as dead
        
    # 2. CACHE MISS / BYPASS -> Check DB
    print(f"Fetching product {product_id} from DB...", flush=True)
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id, ProductDB.isActive == True).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_dict = {
        "id": db_product.id, "name": db_product.name, "description": db_product.description,
        "price": db_product.price, "stockQuantity": db_product.stockQuantity, 
        "category": db_product.category, "isActive": db_product.isActive
    }
    
    # 3. FAULT-TOLERANT CACHE SAVE
    # Only attempt to save if Redis didn't crash during Step 1
    if redis_available:
        try:
            redis_client.set(cache_key, json.dumps(product_dict), ex=3600)
        except Exception as e:
            print(f"REDIS SAVE ERROR: {e}. Silently failing.", flush=True)
    
    return product_dict

@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    # Cache Invalidation
    try:
        redis_client.delete(f"product:{product_id}")
    except Exception:
        pass
    
    return db_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_product.isActive = False
    db.commit()
    
    # Cache Invalidation
    try:
        redis_client.delete(f"product:{product_id}")
    except Exception:
        pass
    
    return {"message": "Product deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)