from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict
import os

from pymongo import MongoClient, ASCENDING

from models import (
    UserBase, UserLogin, WarehouseBase, WarehouseLogin,
    Product, Order, RestockPrediction, StockUpdate
)
from ml_utils import ml_engine, get_sales_from_orders

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smart_supply_chain")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
retailers = db["retailers"]
warehouses = db["warehouses"]
stocks = db["stocks"]
orders = db["orders"]

# Indexes
retailers.create_index([("shop_mobile", ASCENDING)], unique=True)
warehouses.create_index([("mobile", ASCENDING)], unique=True)
stocks.create_index([("warehouse_id", ASCENDING), ("product_id", ASCENDING)], unique=True)
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

def oid(x): 
    return str(x) if isinstance(x, ObjectId) else x

# ---------------- AUTH ----------------
@app.post("/auth/retailer/register")
def register_retailer(data: UserBase):
    if retailers.find_one({"shop_mobile": data.shop_mobile}):
        raise HTTPException(400, "Retailer already exists with this mobile")
    
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    doc["created_at"] = datetime.utcnow()
    res = retailers.insert_one(doc)
    return {"retailer_id": oid(res.inserted_id)}

@app.post("/auth/warehouse/register")
def register_warehouse(data: WarehouseBase):
    if warehouses.find_one({"mobile": data.mobile}):
        raise HTTPException(400, "Warehouse already exists with this mobile")
    
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    doc["created_at"] = datetime.utcnow()
    res = warehouses.insert_one(doc)
    return {"warehouse_id": oid(res.inserted_id)}

@app.post("/auth/retailer/login")
def login_retailer(data: UserLogin):
    u = retailers.find_one({"shop_mobile": data.shop_mobile})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
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
        raise HTTPException(401, "Invalid credentials")
    return {
        "warehouse_id": oid(u["_id"]),
        "name": u["name"],
        "address": u["address"],
        "city": u["city"],
        "region": u["region"]
    }

# ------------- WAREHOUSE OPERATIONS -------------
@app.get("/warehouses/{warehouse_id}/nearby-retailers")
def get_nearby_retailers(warehouse_id: str):
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    # Find retailers in same city/region
    nearby = list(retailers.find(
        {"city": w["city"], "region": w["region"]},
        {"name": 1, "shop_address": 1, "city": 1, "region": 1}
    ))
    
    return {
        "warehouse": {"name": w["name"], "city": w["city"], "region": w["region"]},
        "retailers": [{"retailer_id": oid(r["_id"]), **{k:v for k,v in r.items() if k != "_id"}} 
                     for r in nearby]
    }

@app.post("/warehouses/{warehouse_id}/stock")
def add_stock(warehouse_id: str, stock_items: List[StockUpdate]):
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    for item in stock_items:
        stocks.update_one(
            {"warehouse_id": warehouse_id, "product_id": item.product_id},
            {"$set": {
                "product_name": item.product_name,
                "price": item.price,
                "updated_at": datetime.utcnow()
            }, "$inc": {"quantity": item.quantity}},
            upsert=True
        )
    
    return {"message": f"Updated {len(stock_items)} products"}

@app.get("/warehouses/{warehouse_id}/stock")
def get_warehouse_stock(warehouse_id: str):
    stock_data = list(stocks.find({"warehouse_id": warehouse_id}, {"_id": 0}))
    return {"warehouse_id": warehouse_id, "stock": stock_data}

# ------------- ORDERS -------------
@app.post("/orders")
def place_order(order: Order):
    # Validate retailer and warehouse exist
    r = retailers.find_one({"_id": ObjectId(order.retailer_id)})
    w = warehouses.find_one({"_id": ObjectId(order.warehouse_id)})
    if not r or not w:
        raise HTTPException(404, "Retailer or Warehouse not found")
    
    # Check stock availability
    stock = stocks.find_one({"warehouse_id": order.warehouse_id, "product_id": order.product_id})
    if not stock:
        raise HTTPException(400, f"Product {order.product_name} not available in warehouse")
    
    doc = order.dict()
    doc["status"] = "PENDING"
    doc["created_at"] = datetime.utcnow()
    res = orders.insert_one(doc)
    
    return {"order_id": oid(res.inserted_id), "status": "PENDING"}

@app.get("/orders/warehouse/{warehouse_id}")
def get_warehouse_orders(warehouse_id: str, status: str = None):
    query = {"warehouse_id": warehouse_id}
    if status:
        query["status"] = status.upper()
    
    order_list = list(orders.find(query).sort("created_at", -1))
    for o in order_list:
        o["_id"] = oid(o["_id"])
        o["created_at"] = o["created_at"].isoformat()
    
    return {"orders": order_list}

@app.post("/orders/{order_id}/approve")
def approve_order(order_id: str):
    o = orders.find_one({"_id": ObjectId(order_id)})
    if not o or o["status"] != "PENDING":
        raise HTTPException(400, "Order not found or not pending")
    
    # Check and deduct stock
    stock = stocks.find_one({"warehouse_id": o["warehouse_id"], "product_id": o["product_id"]})
    if not stock or stock["quantity"] < o["quantity"]:
        orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED"}})
        raise HTTPException(400, "Insufficient stock")
    
    # Deduct stock and approve order
    stocks.update_one(
        {"warehouse_id": o["warehouse_id"], "product_id": o["product_id"]},
        {"$inc": {"quantity": -o["quantity"]}}
    )
    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "APPROVED"}})
    
    return {"order_id": order_id, "status": "APPROVED"}

@app.post("/orders/{order_id}/reject")
def reject_order(order_id: str):
    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED"}})
    return {"order_id": order_id, "status": "REJECTED"}

# ------------- AI PREDICTIONS -------------
@app.post("/warehouses/{warehouse_id}/train-models")
def train_prediction_models(warehouse_id: str):
    """Train ML models for all products in warehouse"""
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    # Get all products in warehouse
    warehouse_products = list(stocks.find({"warehouse_id": warehouse_id}))
    
    results = {}
    for product in warehouse_products:
        product_id = product["product_id"]
        
        # Get order history for this product
        order_history = list(orders.find({
            "warehouse_id": warehouse_id,
            "product_id": product_id,
            "status": "APPROVED"
        }))
        
        # Convert orders to sales data
        sales_data = get_sales_from_orders(order_history)
        
        # Train model
        train_result = ml_engine.train_product_model(product_id, sales_data)
        results[product_id] = {
            "product_name": product["product_name"],
            "train_status": train_result["status"],
            "model_type": train_result.get("model_type"),
            "data_points": len(sales_data)
        }
    
    return {"warehouse_id": warehouse_id, "training_results": results}

@app.get("/warehouses/{warehouse_id}/restock-predictions")
def get_restock_predictions(warehouse_id: str):
    """Get AI-powered restock predictions for all products"""
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    # Get all products and their current stock
    warehouse_products = list(stocks.find({"warehouse_id": warehouse_id}))
    
    predictions = []
    for product in warehouse_products:
        product_id = product["product_id"]
        current_stock = product["quantity"]
        
        # Get restock recommendation from ML engine
        recommendation = ml_engine.calculate_restock_recommendation(
            product_id=product_id,
            current_stock=current_stock,
            lead_time_days=3,  # Default lead time
            service_level=0.95
        )
        
        prediction = RestockPrediction(
            product_id=product_id,
            current_stock=current_stock,
            daily_usage=recommendation["avg_daily_demand"],
            days_to_stockout=recommendation["days_to_reorder"],
            suggested_reorder_date=recommendation["reorder_date"],
            suggested_order_qty=recommendation["suggested_order_qty"],
            confidence_level=recommendation["confidence_level"]
        )
        
        predictions.append({
            "product_id": product_id,
            "product_name": product["product_name"],
            "current_stock": current_stock,
            "price": product["price"],
            **recommendation
        })
    
    return {"warehouse_id": warehouse_id, "predictions": predictions}

@app.get("/products/{product_id}/demand-forecast")
def get_demand_forecast(product_id: str, days: int = 14):
    """Get demand forecast for specific product"""
    forecast = ml_engine.predict_demand(product_id, days)
    
    forecast_data = []
    base_date = datetime.now()
    for i, demand in enumerate(forecast):
        forecast_data.append({
            "date": (base_date + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "predicted_demand": round(demand, 2)
        })
    
    return {
        "product_id": product_id,
        "forecast_days": days,
        "forecast": forecast_data,
        "total_predicted_demand": round(sum(forecast), 2)
    }

# ------------- RETAILER DASHBOARD -------------
@app.get("/retailers/{retailer_id}/nearby-warehouses")
def get_nearby_warehouses(retailer_id: str):
    r = retailers.find_one({"_id": ObjectId(retailer_id)})
    if not r:
        raise HTTPException(404, "Retailer not found")
    
    # Find warehouses in same city/region
    nearby = list(warehouses.find(
        {"city": r["city"], "region": r["region"]},
        {"name": 1, "address": 1, "city": 1, "region": 1}
    ))
    
    return {
        "retailer": {"name": r["name"], "city": r["city"], "region": r["region"]},
        "warehouses": [{"warehouse_id": oid(w["_id"]), **{k:v for k,v in w.items() if k != "_id"}} 
                      for w in nearby]
    }

@app.get("/retailers/{retailer_id}/orders")
def get_retailer_orders(retailer_id: str, status: str = None):
    query = {"retailer_id": retailer_id}
    if status:
        query["status"] = status.upper()
    
    order_list = list(orders.find(query).sort("created_at", -1))
    for o in order_list:
        o["_id"] = oid(o["_id"])
        o["created_at"] = o["created_at"].isoformat()
    
    return {"orders": order_list}

@app.get("/warehouses/{warehouse_id}/products")
def get_warehouse_products(warehouse_id: str):
    """Get available products in warehouse for retailers"""
    products = list(stocks.find(
        {"warehouse_id": warehouse_id, "quantity": {"$gt": 0}},
        {"_id": 0}
    ))
    return {"warehouse_id": warehouse_id, "products": products}

# ------------- ANALYTICS -------------
@app.get("/analytics/dashboard/{warehouse_id}")
def get_analytics_dashboard(warehouse_id: str):
    """Get analytics dashboard data"""
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    # Basic statistics
    total_products = stocks.count_documents({"warehouse_id": warehouse_id})
    total_orders = orders.count_documents({"warehouse_id": warehouse_id})
    pending_orders = orders.count_documents({"warehouse_id": warehouse_id, "status": "PENDING"})
    
    # Low stock alerts (less than 10 units)
    low_stock = list(stocks.find({
        "warehouse_id": warehouse_id,
        "quantity": {"$lt": 10}
    }, {"_id": 0}))
    
    # Recent order trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_orders = list(orders.aggregate([
        {"$match": {
            "warehouse_id": warehouse_id,
            "created_at": {"$gte": thirty_days_ago}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "order_count": {"$sum": 1},
            "total_quantity": {"$sum": "$quantity"}
        }},
        {"$sort": {"_id": 1}}
    ]))
    
    return {
        "warehouse_id": warehouse_id,
        "summary": {
            "total_products": total_products,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "low_stock_items": len(low_stock)
        },
        "low_stock_alerts": low_stock,
        "order_trends": recent_orders
    }

if _name_== "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
