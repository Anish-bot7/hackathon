from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ============== AUTH MODELS ==============
class RetailerRegister(BaseModel):
    name: str
    shop_mobile: str
    shop_address: str
    city: str
    region: str
    password: str

class RetailerLogin(BaseModel):
    shop_mobile: str
    password: str

class WarehouseRegister(BaseModel):
    name: str
    mobile: str
    address: str
    city: str
    region: str
    password: str

class WarehouseLogin(BaseModel):
    mobile: str
    password: str

# ============== INVENTORY MODELS ==============
class StockItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float = 0.0

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int

class OrderCreate(BaseModel):
    retailer_id: str
    warehouse_id: str
    items: List[OrderItem]

# ============== ML MODELS ==============
class PredictionRequest(BaseModel):
    retailer_id: str
    current_stock: Dict[str, int]

class RestockRecommendation(BaseModel):
    product_id: str
    current_stock: int
    predicted_demand: float
    days_to_stockout: float
    reorder_point: int
    suggested_order_qty: int
    confidence: str