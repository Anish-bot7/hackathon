from pydantic import BaseModel, Field
from typing import List, Dict

# ------------------- User Models -------------------
class UserBase(BaseModel):
    name: str
    email: str
    password: str
    location_name: str
    lat: float
    lng: float

class RetailerIn(UserBase):
    """Retailer registration input"""
    pass

class WarehouseIn(UserBase):
    """Warehouse registration input"""
    pass

class LoginIn(BaseModel):
    email: str
    password: str

# ------------------- Stock / Orders -------------------
class StockItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class OrderIn(BaseModel):
    retailer_id: str
    warehouse_id: str
    items: List[OrderItem]

class OrderOut(BaseModel):
    order_id: str
    status: str

# ------------------- ML Prediction -------------------
class PredictInput(BaseModel):
    # optional: provide on-hand inventory snapshot (per product) for better prediction
    current_on_hand: Dict[str, int] = Field(default_factory=dict)
