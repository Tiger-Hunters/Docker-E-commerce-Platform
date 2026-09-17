from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import redis
import json

app = FastAPI()

# --- Connect to Redis Container ---
# 'redis' is the exact service name from our docker-compose.yml
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# --- Custom Error Handler ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# --- In-Memory Database ---
fake_product_db = {}
product_id_counter = 101

# --- Pydantic Models ---
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stockQuantity: int
    category: str

class ProductUpdate(BaseModel):
    name: str
    description: str
    price: float
    stockQuantity: int
    category: str

class ProductResponse(BaseModel):
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
def create_product(product: ProductCreate):
    global product_id_counter
    
    new_product = product.dict()
    new_product["id"] = product_id_counter
    new_product["isActive"] = True
    
    fake_product_db[product_id_counter] = new_product
    product_id_counter += 1
    
    return new_product

@app.get("/api/products", response_model=list[ProductResponse])
def get_all_products():
    # Return only active products
    return [p for p in fake_product_db.values() if p["isActive"]]

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    cache_key = f"product:{product_id}"
    
    # 1. Check Redis Cache First (HIT)
    cached_product = redis_client.get(cache_key)
    if cached_product:
        print("REDIS HIT!") # You'll see this in Docker logs
        return json.loads(cached_product)
        
    # 2. If not in cache (MISS), check Database
    print("REDIS MISS! Fetching from DB...")
    if product_id not in fake_product_db:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product = fake_product_db[product_id]
    
    # 3. Save to Redis for next time (Cache it for 60 seconds)
    redis_client.setex(cache_key, 60, json.dumps(product))
    
    return product

@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):
    if product_id not in fake_product_db:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Update DB
    updated_data = product.dict()
    updated_data["id"] = product_id
    updated_data["isActive"] = fake_product_db[product_id]["isActive"]
    fake_product_db[product_id] = updated_data
    
    # Update Redis Cache (Invalidation / Sync)
    cache_key = f"product:{product_id}"
    redis_client.setex(cache_key, 60, json.dumps(updated_data))
    
    return updated_data

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    if product_id not in fake_product_db:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Soft Delete (isActive = false)
    fake_product_db[product_id]["isActive"] = False
    
    # Remove from cache so users don't see deleted items!
    redis_client.delete(f"product:{product_id}")
    
    return {"message": "Product deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)