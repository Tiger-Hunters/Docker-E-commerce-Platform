from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn
import requests
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# --- Database Setup ---
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
DB_HOST = os.getenv("DB_HOST", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/order_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
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
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # 1. Verify User
    try:
        user_res = requests.get(f"http://user-service:5001/api/users/{order.userId}")
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
def get_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@app.get("/api/users/{user_id}/orders", response_model=list[OrderResponse])
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    return db.query(OrderDB).filter(OrderDB.userId == user_id).all()

@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    db_order.status = status_update.status
    db.commit()
    return {"id": order_id, "status": status_update.status}

@app.delete("/api/orders/{order_id}")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    db_order.status = "CANCELLED"
    db.commit()
    return {"message": "Order cancelled successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)