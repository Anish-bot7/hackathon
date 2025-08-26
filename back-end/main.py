from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from pydantic import BaseModel
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("smart_supply_chain")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI(title="Smart Supply Chain API")

# Pydantic models
class RetailerRegister(BaseModel):
    shop_name: str
    location: str
    password: str

class RetailerLogin(BaseModel):
    shop_name: str
    password: str

class WarehouseRegister(BaseModel):
    owner_name: str
    location: str
    password: str

class WarehouseLogin(BaseModel):
    owner_name: str
    password: str


# ✅ Register Retailer
@app.post("/register/retailer")
def register_retailer(data: RetailerRegister):
    existing = db.retailers.find_one({"shop_name": data.shop_name})
    if existing:
        raise HTTPException(status_code=400, detail="Shop already registered")

    hashed_pw = pwd_context.hash(data.password)
    db.retailers.insert_one({
        "shop_name": data.shop_name,
        "location": data.location,
        "password": hashed_pw
    })
    return {"msg": "Retailer registered successfully"}


# ✅ Login Retailer
@app.post("/login/retailer")
def login_retailer(data: RetailerLogin):
    retailer = db.retailers.find_one({"shop_name": data.shop_name})
    if not retailer or not pwd_context.verify(data.password, retailer["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"msg": "Retailer login successful"}


# ✅ Register Warehouse
@app.post("/register/warehouse")
def register_warehouse(data: WarehouseRegister):
    existing = db.warehouses.find_one({"owner_name": data.owner_name})
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse already registered")

    hashed_pw = pwd_context.hash(data.password)
    db.warehouses.insert_one({
        "owner_name": data.owner_name,
        "location": data.location,
        "password": hashed_pw
    })
    return {"msg": "Warehouse registered successfully"}


# ✅ Login Warehouse
@app.post("/login/warehouse")
def login_warehouse(data: WarehouseLogin):
    warehouse = db.warehouses.find_one({"owner_name": data.owner_name})
    if not warehouse or not pwd_context.verify(data.password, warehouse["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"msg": "Warehouse login successful"}
