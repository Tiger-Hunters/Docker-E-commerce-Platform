from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import requests
from datetime import datetime

app = FastAPI()

# --- Custom Error Handler ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# --- In-Memory Database ---
fake_order_db = {}
order_id_counter = 1001

# --- Pydantic Models ---
class OrderItemCreate(BaseModel):
    productId: int
    quantity: int

class OrderCreate(BaseModel):
    userId: int
    items: list[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str

# --- API Routes ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    global order_id_counter
    
    # 1. Verify User exists by calling User Service internally
    try:
        user_res = requests.get(f"http://user-service:5001/api/users/{order.userId}")
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid User ID")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="User Service is down")

    # 2. Fetch Products and Calculate Totals
    processed_items = []
    total_amount = 0.0

    for item in order.items:
        try:
            prod_res = requests.get(f"http://product-service:5002/api/products/{item.productId}")
            if prod_res.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Product {item.productId} not found")
            
            product_data = prod_res.json()
            unit_price = product_data["price"]
            subtotal = unit_price * item.quantity
            total_amount += subtotal
            
            processed_items.append({
                "productId": item.productId,
                "quantity": item.quantity,
                "unitPrice": unit_price,
                "subtotal": subtotal
            })
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=500, detail="Product Service is down")

    # 3. Create and Save the Order
    new_order = {
        "id": order_id_counter,
        "userId": order.userId,
        "items": processed_items,
        "totalAmount": total_amount,
        "status": "PENDING",
        "createdAt": datetime.now().isoformat()
    }
    
    fake_order_db[order_id_counter] = new_order
    order_id_counter += 1
    
    return new_order

@app.get("/api/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in fake_order_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return fake_order_db[order_id]

@app.get("/api/users/{user_id}/orders")
def get_user_orders(user_id: int):
    # Filter orders for a specific user
    user_orders = [o for o in fake_order_db.values() if o["userId"] == user_id]
    return user_orders

@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusUpdate):
    if order_id not in fake_order_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    fake_order_db[order_id]["status"] = status_update.status
    return {"id": order_id, "status": status_update.status}

@app.delete("/api/orders/{order_id}")
def cancel_order(order_id: int):
    if order_id not in fake_order_db:
        raise HTTPException(status_code=404, detail="Order not found")
        
    fake_order_db[order_id]["status"] = "CANCELLED"
    return {"message": "Order cancelled successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)