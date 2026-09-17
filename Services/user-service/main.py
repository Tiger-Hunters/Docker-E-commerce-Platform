from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# --- Custom Error Handler to match API Contract ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# --- In-Memory Database (Replace with Postgres/Mongo later) ---
fake_user_db = {}
user_id_counter = 1

# --- Pydantic Models (Enforcing the Data Field Agreement) ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
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
def create_user(user: UserCreate):
    global user_id_counter
    
    # Check if email exists
    for u in fake_user_db.values():
        if u["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email already exists")
    
    # Save user (using passwordHash internally as per contract)
    new_user = {
        "id": user_id_counter,
        "name": user.name,
        "email": user.email,
        "passwordHash": user.password + "_hashed" # Mock hashing
    }
    fake_user_db[user_id_counter] = new_user
    user_id_counter += 1
    
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    if user_id not in fake_user_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_user_db[user_id]

@app.post("/api/users/login", response_model=LoginResponse)
def login(credentials: UserLogin):
    for u in fake_user_db.values():
        if u["email"] == credentials.email and u["passwordHash"] == credentials.password + "_hashed":
            return {
                "token": "jwt-token-here",
                "user": u
            }
    raise HTTPException(status_code=401, detail="Invalid email or password")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)