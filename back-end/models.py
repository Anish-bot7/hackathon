from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ------------------- User Models -------------------
class UserBase(BaseModel):
    name: str
    shop_mobile: str
    shop_address: str
    city: str
    region: str
    password: str

class UserLogin(BaseModel):
    shop_mobile: str
    password: str

# ------------------- Warehouse Models -------------------
class WarehouseBase(BaseModel):
    name: str
    mobile: str
    address: str
    city: str
    region: str
    password: str

class WarehouseLogin(BaseModel):
    mobile: str
    password: str

# ------------------- Product Models -------------------
class Product(BaseModel):
    warehouse_id: str
    product_name: str
    product_id: str
    quantity: int
    price: float

class StockUpdate(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float

# ------------------- Order Models -------------------
class Order(BaseModel):
    retailer_id: str
    warehouse_id: str
    product_name: str
    product_id: str
    quantity: int

# ------------------- ML Prediction Models -------------------
class RestockPrediction(BaseModel):
    product_id: str
    current_stock: int
    daily_usage: float
    days_to_stockout: float
    suggested_reorder_date: str
    suggested_order_qty: int
    confidence_level: str  # "HIGH", "MEDIUM", "LOW"

class SalesRecord(BaseModel):
    date: datetime
    product_id: str
    quantity: int
    retailer_id: Optional[str]= None