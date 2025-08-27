from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
from typing import List, Dict
import os

from pymongo import MongoClient, ASCENDING

from models import RetailerIn, WarehouseIn, LoginIn, StockItem, OrderIn, OrderOut, PredictInput
from ml_utils import nearest_within_km, estimate_daily_usage_from_orders, predict_days_to_stockout

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "smart_supply_chain")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI missing in .env")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
retailers = db["retailers"]
warehouses = db["warehouses"]
stocks = db["stocks"]             # warehouse stock: {warehouse_id, product_id, product_name, quantity}
orders = db["orders"]             # retailer orders to warehouse
default_orders = db["default_orders"]  # remembered last successful order per retailer

# Indexes
retailers.create_index([("email", ASCENDING)], unique=True)
warehouses.create_index([("email", ASCENDING)], unique=True)
stocks.create_index([("warehouse_id", ASCENDING)])
orders.create_index([("retailer_id", ASCENDING), ("warehouse_id", ASCENDING), ("created_at", ASCENDING)])

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Smart Supply Chain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def oid(x): return str(x) if isinstance(x, ObjectId) else x

# ---------------- AUTH ----------------
@app.post("/auth/retailer/register")
def register_retailer(data: RetailerIn):
    if retailers.find_one({"email": data.email}):
        raise HTTPException(400, "Retailer email already exists")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    res = retailers.insert_one(doc)
    return {"retailer_id": oid(res.inserted_id)}

@app.post("/auth/retailer/login")
def login_retailer(data: LoginIn):
    u = retailers.find_one({"email": data.email})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    return {
        "retailer_id": oid(u["_id"]),
        "name": u["name"],
        "location_name": u["location_name"],
        "lat": u["lat"],
        "lng": u["lng"]
    }

@app.post("/auth/warehouse/register")
def register_warehouse(data: WarehouseIn):
    if warehouses.find_one({"email": data.email}):
        raise HTTPException(400, "Warehouse email already exists")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    res = warehouses.insert_one(doc)
    return {"warehouse_id": oid(res.inserted_id)}

@app.post("/auth/warehouse/login")
def login_warehouse(data: LoginIn):
    u = warehouses.find_one({"email": data.email})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    return {
        "warehouse_id": oid(u["_id"]),
        "name": u["name"],
        "location_name": u["location_name"],
        "lat": u["lat"],
        "lng": u["lng"]
    }

# ------------- RETAILER DASHBOARD -------------
@app.get("/retailers/{retailer_id}/nearby-warehouses")
def get_nearby_warehouses(retailer_id: str, radius_km: float = 10.0):
    r = retailers.find_one({"_id": ObjectId(retailer_id)})
    if not r: raise HTTPException(404, "Retailer not found")
    origin = (r["lat"], r["lng"])
    cands = []
    for w in warehouses.find({}, {"name":1,"location_name":1,"lat":1,"lng":1}):
        cands.append({"_id": oid(w["_id"]), "name": w["name"], "location_name": w["location_name"], "lat": w["lat"], "lng": w["lng"]})
    near = nearest_within_km(origin, cands, radius_km)
    return {"retailer": {"name": r["name"], "location_name": r["location_name"]}, "warehouses": near}

@app.get("/warehouses/{warehouse_id}/stock")
def get_warehouse_stock(warehouse_id: str):
    data = list(stocks.find({"warehouse_id": warehouse_id}, {"_id":0}))
    return {"warehouse_id": warehouse_id, "stock": data}

@app.post("/orders", response_model=OrderOut)
def place_order(order: OrderIn):
    # basic validation
    r = retailers.find_one({"_id": ObjectId(order.retailer_id)})
    w = warehouses.find_one({"_id": ObjectId(order.warehouse_id)})
    if not r or not w:
        raise HTTPException(404, "Retailer or Warehouse not found")

    # check stock availability
    # (simple check: sufficient quantity for each product)
    for it in order.items:
        s = stocks.find_one({"warehouse_id": order.warehouse_id, "product_id": it.product_id})
        if not s or s["quantity"] < it.quantity:
            raise HTTPException(400, f"Insufficient stock for {it.product_id}")

    # deduct stock
    for it in order.items:
        stocks.update_one(
            {"warehouse_id": order.warehouse_id, "product_id": it.product_id},
            {"$inc": {"quantity": -int(it.quantity)}}
        )

    doc = {
        "retailer_id": order.retailer_id,
        "warehouse_id": order.warehouse_id,
        "items": [i.dict() for i in order.items],
        "status": "PLACED",
        "created_at": datetime.utcnow(),
        "notify_warehouse": True  # Warehouse dashboard can filter for this
    }
    res = orders.insert_one(doc)

    # remember as default order
    default_orders.update_one(
        {"retailer_id": order.retailer_id},
        {"$set": {"retailer_id": order.retailer_id, "items": [i.dict() for i in order.items]}},
        upsert=True
    )

    return {"order_id": oid(res.inserted_id), "status": "PLACED"}

@app.get("/retailers/{retailer_id}/default-order")
def get_default_order(retailer_id: str):
    d = default_orders.find_one({"retailer_id": retailer_id}, {"_id":0})
    return d or {"retailer_id": retailer_id, "items": []}

# ------------- WAREHOUSE DASHBOARD -------------
@app.get("/warehouses/{warehouse_id}/orders")
def get_warehouse_orders(warehouse_id: str):
    data = list(orders.find({"warehouse_id": warehouse_id}).sort("created_at", -1))
    formatted = []
    for o in data:
        formatted.append({
            "order_id": oid(o["_id"]),
            "retailer_id": o["retailer_id"],
            "items": o["items"],
            "status": o.get("status", "PLACED"),
            "created_at": o["created_at"]
        })
    return {"orders": formatted}

@app.post("/warehouses/{warehouse_id}/stock")
def upsert_warehouse_stock(warehouse_id: str, items: List[StockItem]):
    # add/update stock for warehouse
    for it in items:
        stocks.update_one(
            {"warehouse_id": warehouse_id, "product_id": it.product_id},
            {"$set": {"product_name": it.product_name}, "$inc": {"quantity": int(it.quantity)}},
            upsert=True
        )
    return {"ok": True}

# ------------- ML: Stock finish prediction -------------
@app.post("/retailers/{retailer_id}/predict-stockout")
def predict_stockout(retailer_id: str, payload: PredictInput):
    # use order history to estimate usage
    hist = list(orders.find({"retailer_id": retailer_id}))
    daily_usage = estimate_daily_usage_from_orders(hist)

    # If current_on_hand not provided, infer ZERO (will suggest reorder)
    current = payload.current_on_hand or {}

    days_left = predict_days_to_stockout(current, daily_usage)
    # build recommendations
    notifications = []
    for pid, days in days_left.items():
        if days <= 3.0:
            notifications.append({"product_id": pid, "message": f"Low horizon: {days} days left. Consider reordering."})
    return {"daily_usage": daily_usage, "days_to_stockout": days_left, "notifications": notifications}
