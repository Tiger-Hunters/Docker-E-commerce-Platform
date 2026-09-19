from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn
import requests
import os
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from pathlib import Path
from sqlalchemy.engine import URL
import jwt

# --- Database Setup ---

DB_USER = os.getenv("DB_USER", "ecom_user")
DB_HOST = os.getenv("DB_HOST", "localhost")

def read_secret():
    secret_file = os.getenv("DB_PASSWORD_FILE")
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()

    # Optional fallback for local development only
    return os.getenv("DB_PASSWORD", "secret")

DB_PASSWORD = read_secret()

DATABASE_URL = URL.create(
    drivername="postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database="order_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False)
    totalAmount = Column(Float, nullable=False)
    status = Column(String, default="PENDING")
    createdAt = Column(String, nullable=False)
    items = relationship("OrderItemDB", back_populates="order")

class OrderItemDB(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    orderId = Column(Integer, ForeignKey("orders.id"))
    productId = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    unitPrice = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    order = relationship("OrderDB", back_populates="items")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
class OrderItemCreate(BaseModel):
    productId: int
    quantity: int

class OrderCreate(BaseModel):
    userId: int
    items: list[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    productId: int
    quantity: int
    unitPrice: float
    subtotal: float

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    userId: int
    totalAmount: float
    status: str
    createdAt: str
    items: list[OrderItemResponse]

# --- API Routes ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate,current_user_id: int = Depends(get_current_user),credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),db: Session = Depends(get_db)):
    if order.userId != current_user_id:
        raise HTTPException(status_code=403,detail="You cannot create orders for another user")
    # 1. Verify User
    try:
        user_res = requests.get(f"http://user-service:5001/api/users/{order.userId}",headers={"Authorization": f"Bearer {credentials.credentials}"})
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid User ID")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="User Service is down")

    # 2. Fetch Products and Calculate Totals
    total_amount = 0.0
    db_items = []

    for item in order.items:
        try:
            prod_res = requests.get(f"http://product-service:5002/api/products/{item.productId}")
            if prod_res.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Product {item.productId} not found")
            
            product_data = prod_res.json()
            unit_price = product_data["price"]
            subtotal = unit_price * item.quantity
            total_amount += subtotal
            
            db_items.append(OrderItemDB(
                productId=item.productId,
                quantity=item.quantity,
                unitPrice=unit_price,
                subtotal=subtotal
            ))
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=500, detail="Product Service is down")

    # 3. Create and Save Order
    new_order = OrderDB(
        userId=order.userId,
        totalAmount=total_amount,
        status="PENDING",
        createdAt=datetime.now().isoformat()
    )
    new_order.items = db_items
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return new_order

@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.userId != current_user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to access this order")
    return db_order

@app.get("/api/users/{user_id}/orders", response_model=list[OrderResponse])
def get_user_orders(user_id: int, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to access these orders")
    return db.query(OrderDB).filter(OrderDB.userId == user_id).all()

@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.userId != current_user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to modify this order")
    
    valid_statuses = ["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    db_order.status = status_update.status
    db.commit()
    return {"id": order_id, "status": status_update.status}

@app.delete("/api/orders/{order_id}")
def cancel_order(order_id: int, current_user_id: int = Depends(get_current_user),db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.userId != current_user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to cancel this order")
        
    db_order.status = "CANCELLED"
    db.commit()
    return {"message": "Order cancelled successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)