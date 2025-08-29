from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
from typing import List
import os

from pymongo import MongoClient, ASCENDING

from models import (
    UserBase, UserLogin,
    WarehouseBase, WarehouseLogin,
    Product, Order
)
from ml_utils import estimate_daily_usage_from_orders, predict_days_to_stockout

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "smart_supply_chain")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI missing in .env")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


retailers = db["retailers"]
warehouses = db["warehouses"]
stocks = db["stocks"]             # warehouse stock
orders = db["orders"]             # retailer orders
default_orders = db["default_orders"]


retailers.create_index([("shop_mobile", ASCENDING), ("city", ASCENDING)], unique=True)
warehouses.create_index([("mobile", ASCENDING), ("city", ASCENDING)], unique=True)
stocks.create_index([("warehouse_id", ASCENDING)])
orders.create_index([("retailer_id", ASCENDING), ("warehouse_id", ASCENDING), ("created_at", ASCENDING)])

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Smart Supply Chain API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def oid(x): return str(x) if isinstance(x, ObjectId) else x


@app.post("/auth/retailer/register")
def register_retailer(data: UserBase):
    if retailers.find_one({"shop_mobile": data.shop_mobile}):
        raise HTTPException(400, "Retailer already exists in this city with same mobile")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"]) 
    res = retailers.insert_one(doc)
    return {"retailer_id": oid(res.inserted_id)}

@app.post("/auth/warehouse/register")
def register_warehouse(data: WarehouseBase):
    if warehouses.find_one({"mobile": data.mobile}):
        raise HTTPException(400, "Warehouse already exists in this city with same mobile")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])  
    res = warehouses.insert_one(doc)
    return {"warehouse_id": oid(res.inserted_id)}

@app.post("/auth/retailer/login")
def login_retailer(data: UserLogin):
    u = retailers.find_one({"shop_mobile": data.shop_mobile})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid retailer credentials")
    return {
        "retailer_id": oid(u["_id"]),
        "name": u["name"],
        "shop_address": u["shop_address"],
        "city": u["city"],
        "region": u["region"]
    }

@app.post("/auth/warehouse/login")
def login_warehouse(data: WarehouseLogin):
    u = warehouses.find_one({"mobile": data.mobile})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid warehouse credentials")
    return {
        "warehouse_id": oid(u["_id"]),
        "name": u["name"],
        "address": u["address"],
        "city": u["city"],
        "region": u["region"]
    }


@app.get("/retailers/{retailer_id}/nearby-warehouses")
def get_nearby_warehouses(retailer_id: str):
    r = retailers.find_one({"_id": ObjectId(retailer_id)})
    if not r:
        raise HTTPException(404, "Retailer not found")

   
    city_matches = list(warehouses.find({"city": r["city"]}, {"name":1,"city":1,"region":1}))

    region_matches = [w for w in city_matches if w["region"] == r["region"]]

    warehouses_final = region_matches if region_matches else city_matches

    return {
        "retailer": {
            "name": r["name"],
            "city": r["city"],
            "region": r["region"]
        },
        "warehouses": [
            {
                "warehouse_id": oid(w["_id"]),
                "name": w["name"],
                "city": w["city"],
                "region": w["region"]
            }
            for w in warehouses_final
        ]
    }


@app.post("/stocks")
def add_stock(stock: Product):
    w = warehouses.find_one({"_id": ObjectId(stock.warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")

    doc = stock.dict()
    existing = stocks.find_one({"warehouse_id": stock.warehouse_id, "product_id": stock.product_id})
    if existing:
        stocks.update_one({"_id": existing["_id"]}, {"$inc": {"quantity": stock.quantity}})
        return {"message": "Stock updated"}
    else:
        res = stocks.insert_one(doc)
        return {"id": oid(res.inserted_id), "message": "Stock added"}

@app.get("/warehouses/{warehouse_id}/stocks")
def get_warehouse_stocks(warehouse_id: str):
    data = list(stocks.find({"warehouse_id": warehouse_id}))
    for d in data:
        d["_id"] = oid(d["_id"])
    return data

@app.get("/warehouses/{warehouse_id}/stock")
def get_warehouse_stock(warehouse_id: str):
    data = list(stocks.find({"warehouse_id": warehouse_id}, {"_id":0}))
    return {"warehouse_id": warehouse_id, "stock": data}

@app.post("/warehouses/{warehouse_id}/stock")
def upsert_warehouse_stock(warehouse_id: str, items: List[Product]):
    for it in items:
        stocks.update_one(
            {"warehouse_id": warehouse_id, "product_name": it.product_name},
            {"$set": {"price": it.price}, "$inc": {"quantity": int(it.quantity)}},
            upsert=True
        )
    return {"ok": True}

# ------------- ORDERS -------------
# ----------------- PLACE ORDER (Retailer) -----------------
@app.post("/orders")
def place_order(order: Order):
    r = retailers.find_one({"_id": ObjectId(order.retailer_id)})
    w = warehouses.find_one({"_id": ObjectId(order.warehouse_id)})
    if not r or not w:
        raise HTTPException(404, "Retailer or Warehouse not found")

    # Check if product exists in stock
    s = stocks.find_one({"warehouse_id": order.warehouse_id, "product_id": order.product_id})
    if not s:
        raise HTTPException(400, f"Product {order.product_name} not found in warehouse")

    # Create order with PENDING status (no stock deduction yet)
    doc = {
        "retailer_id": order.retailer_id,
        "warehouse_id": order.warehouse_id,
        "product_id": order.product_id,
        "product_name": order.product_name,
        "quantity": order.quantity,
        "status": "PENDING",
        "created_at": datetime.utcnow()
    }
    res = orders.insert_one(doc)

    return {"order_id": oid(res.inserted_id), "status": "PENDING"}


# ----------------- APPROVE ORDER (Warehouse) -----------------
@app.post("/orders/{order_id}/approve")
def approve_order(order_id: str):
    o = orders.find_one({"_id": ObjectId(order_id)})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["status"] != "PENDING":
        raise HTTPException(400, "Order is not pending")

    # Check stock availability
    s = stocks.find_one({"warehouse_id": o["warehouse_id"], "product_id": o["product_id"]})
    if not s or s["quantity"] < o["quantity"]:
        orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED"}})
        raise HTTPException(400, f"Insufficient stock for {o['product_name']}")

    # Deduct stock
    stocks.update_one(
        {"warehouse_id": o["warehouse_id"], "product_id": o["product_id"]},
        {"$inc": {"quantity": -int(o["quantity"])}}
    )

    # Mark as approved
    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "APPROVED"}})
    return {"order_id": order_id, "status": "APPROVED"}


# ----------------- REJECT ORDER (Warehouse) -----------------
@app.post("/orders/{order_id}/reject")
def reject_order(order_id: str):
    o = orders.find_one({"_id": ObjectId(order_id)})
    if not o:
        raise HTTPException(404, "Order not found")
    if o["status"] != "PENDING":
        raise HTTPException(400, "Order is not pending")

    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED"}})
    return {"order_id": order_id, "status": "REJECTED"}


# ------------- ML: Stock finish prediction -------------
@app.post("/retailers/{retailer_id}/predict-stockout")
def predict_stockout(retailer_id: str, payload: dict):
    hist = list(orders.find({"retailer_id": retailer_id}))
    daily_usage = estimate_daily_usage_from_orders(hist)
    current = payload.get("current_on_hand", {}) or {}
    days_left = predict_days_to_stockout(current, daily_usage)

    notifications = []
    for pid, days in days_left.items():
        if days <= 3.0:
            notifications.append({
                "product_id": pid,
                "message": f"Low horizon: {days} days left. Consider reordering."
            })
    return {"daily_usage": daily_usage, "days_to_stockout": days_left, "notifications": notifications}
