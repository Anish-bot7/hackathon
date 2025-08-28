from pydantic import BaseModel

# ------------------- User Models -------------------
class UserBase(BaseModel):
    name: str
    shop_mobile: str
    shop_address: str
    city: str
    region: str
    password: str   # ✅ Added password here


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
    password: str   # ✅ Added password here


class WarehouseLogin(BaseModel):
    mobile: str
    password: str


# ------------------- Product Models -------------------
class Product(BaseModel):
    warehouse_id: str
    product_name: str
    quantity: int
    price: float


# ------------------- Order Models -------------------
class Order(BaseModel):
    retailer_id: str
    warehouse_id: str
    product_name:str
    product_id: str
    quantity: int
