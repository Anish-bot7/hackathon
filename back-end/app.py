from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ============== MODELS ==============
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

# ============== ML ENGINE ==============
class MLEngine:
    def __init__(self):
        self.models = {}
        self.product_stats = {}
        self.min_data_points = 14
        
    def train_product_model(self, product_id: str, sales_data: List[Dict]) -> Dict:
        """Train ML model for product demand prediction"""
        if len(sales_data) < self.min_data_points:
            return {"status": "insufficient_data", "model_type": None, "data_points": len(sales_data)}
        
        # Convert to DataFrame
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Create features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_num'] = (df['date'] - df['date'].min()).dt.days
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Lag features
        max_lags = min(7, len(df) // 2)
        for i in range(1, max_lags + 1):
            df[f'lag_{i}'] = df['quantity'].shift(i)
        
        # Rolling statistics
        df['ma_3'] = df['quantity'].rolling(3, min_periods=1).mean()
        df['ma_7'] = df['quantity'].rolling(7, min_periods=1).mean()
        df['std_7'] = df['quantity'].rolling(7, min_periods=1).std().fillna(0)
        
        # Remove NaN rows
        df_clean = df.dropna()
        
        if len(df_clean) < 5:
            return {"status": "insufficient_clean_data", "model_type": None}
        
        # Prepare features and target
        feature_cols = [col for col in df_clean.columns if col not in ['date', 'quantity', 'product_id']]
        X = df_clean[feature_cols]
        y = df_clean['quantity']
        
        # Choose model based on data size and pattern
        volatility = np.std(y) / np.mean(y) if np.mean(y) > 0 else 0
        
        if len(sales_data) >= 50 and volatility > 0.4:
            model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
            model_type = "random_forest"
        else:
            model = LinearRegression()
            model_type = "linear_regression"
        
        # Train model
        model.fit(X, y)
        
        # Store model
        self.models[product_id] = {
            "model": model,
            "model_type": model_type,
            "feature_cols": feature_cols,
            "last_data": df_clean.iloc[-1].to_dict(),
            "avg_demand": np.mean(y),
            "volatility": volatility
        }
        
        return {"status": "success", "model_type": model_type, "data_points": len(sales_data)}
    
    def predict_demand(self, product_id: str, days: int = 7) -> List[float]:
        """Predict daily demand for next N days"""
        if product_id not in self.models:
            return [1.0] * days  # Default fallback
        
        model_info = self.models[product_id]
        model = model_info["model"]
        feature_cols = model_info["feature_cols"]
        last_data = model_info["last_data"].copy()
        
        predictions = []
        
        for day in range(days):
            # Prepare features
            X_pred = np.array([last_data.get(col, 0) for col in feature_cols]).reshape(1, -1)
            pred = max(0, model.predict(X_pred)[0])
            predictions.append(pred)
            
            # Update features for next prediction
            last_data['day_num'] += 1
            last_data['day_of_week'] = (last_data['day_of_week'] + 1) % 7
            last_data['is_weekend'] = 1 if last_data['day_of_week'] >= 5 else 0
            
            # Update lag features
            for i in range(7, 1, -1):
                if f'lag_{i}' in last_data:
                    last_data[f'lag_{i}'] = last_data.get(f'lag_{i-1}', pred)
            if 'lag_1' in last_data:
                last_data['lag_1'] = pred
        
        return predictions
    
    def get_restock_recommendation(self, product_id: str, current_stock: int, lead_time_days: int = 3) -> Dict:
        """Calculate restock recommendations"""
        
        # Get demand forecast
        forecast_days = lead_time_days + 7  # Lead time + review period
        demand_forecast = self.predict_demand(product_id, forecast_days)
        
        # Calculate metrics
        avg_daily_demand = np.mean(demand_forecast)
        total_demand = sum(demand_forecast)
        demand_std = np.std(demand_forecast) if len(demand_forecast) > 1 else avg_daily_demand * 0.2
        
        # Safety stock (95% service level)
        safety_stock = 1.96 * demand_std * np.sqrt(lead_time_days)
        reorder_point = avg_daily_demand * lead_time_days + safety_stock
        
        # Days until reorder needed
        days_to_reorder = 0
        projected_stock = current_stock
        
        for daily_demand in demand_forecast:
            if projected_stock <= reorder_point:
                break
            projected_stock -= daily_demand
            days_to_reorder += 1
        
        # Order quantity
        order_qty = max(0, total_demand + safety_stock - current_stock)
        
        # Confidence level
        confidence = "HIGH" if product_id in self.models else "LOW"
        
        reorder_date = datetime.now() + timedelta(days=days_to_reorder)
        
        return {
            "avg_daily_demand": round(avg_daily_demand, 2),
            "reorder_point": round(reorder_point, 2),
            "safety_stock": round(safety_stock, 2),
            "days_to_reorder": days_to_reorder,
            "reorder_date": reorder_date.strftime("%Y-%m-%d"),
            "suggested_order_qty": int(np.ceil(order_qty)),
            "confidence_level": confidence,
            "total_forecast_demand": round(total_demand, 2)
        }

# Database setup
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client[os.getenv("DB_NAME", "smart_supply_chain")]

retailers = db["retailers"]
warehouses = db["warehouses"]
stocks = db["stocks"]
orders = db["orders"]

# Create indexes
try:
    retailers.create_index([("shop_mobile", ASCENDING)], unique=True)
    warehouses.create_index([("mobile", ASCENDING)], unique=True)
    stocks.create_index([("warehouse_id", ASCENDING), ("product_id", ASCENDING)], unique=True)
except:
    pass  # Ignore duplicate key errors

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ml_engine = MLEngine()

app = FastAPI(title="Smart Supply Chain API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def oid(x): 
    return str(x) if isinstance(x, ObjectId) else x

# ============== AUTH ==============
@app.post("/auth/retailer/register")
def register_retailer(data: RetailerRegister):
    if retailers.find_one({"shop_mobile": data.shop_mobile}):
        raise HTTPException(400, "Mobile number already exists")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    doc["created_at"] = datetime.utcnow()
    res = retailers.insert_one(doc)
    return {"retailer_id": oid(res.inserted_id)}

@app.post("/auth/retailer/login")
def login_retailer(data: RetailerLogin):
    u = retailers.find_one({"shop_mobile": data.shop_mobile})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    return {"retailer_id": oid(u["_id"]), "name": u["name"], "city": u["city"], "region": u["region"]}

@app.post("/auth/warehouse/register")
def register_warehouse(data: WarehouseRegister):
    if warehouses.find_one({"mobile": data.mobile}):
        raise HTTPException(400, "Mobile number already exists")
    doc = data.dict()
    doc["password"] = pwd.hash(doc["password"])
    doc["created_at"] = datetime.utcnow()
    res = warehouses.insert_one(doc)
    return {"warehouse_id": oid(res.inserted_id)}

@app.post("/auth/warehouse/login")
def login_warehouse(data: WarehouseLogin):
    u = warehouses.find_one({"mobile": data.mobile})
    if not u or not pwd.verify(data.password, u["password"]):
        raise HTTPException(401, "Invalid credentials")
    return {"warehouse_id": oid(u["_id"]), "name": u["name"], "city": u["city"], "region": u["region"]}

# ============== WAREHOUSE OPERATIONS ==============
@app.post("/warehouses/{warehouse_id}/stock")
def add_stock(warehouse_id: str, stock_items: List[StockItem]):
    w = warehouses.find_one({"_id": ObjectId(warehouse_id)})
    if not w:
        raise HTTPException(404, "Warehouse not found")
    
    for item in stock_items:
        stocks.update_one(
            {"warehouse_id": warehouse_id, "product_id": item.product_id},
            {"$set": {"product_name": item.product_name, "price": item.price, "updated_at": datetime.utcnow()}, 
             "$inc": {"quantity": item.quantity}},
            upsert=True
        )
    return {"message": f"Updated {len(stock_items)} products"}

@app.get("/warehouses/{warehouse_id}/stock")
def get_warehouse_stock(warehouse_id: str):
    stock_data = list(stocks.find({"warehouse_id": warehouse_id}, {"_id": 0}))
    return {"warehouse_id": warehouse_id, "stock": stock_data}

@app.get("/warehouses/{warehouse_id}/orders")
def get_warehouse_orders(warehouse_id: str, status: Optional[str] = None):
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
    
    # Check stock and deduct
    for item in o["items"]:
        stock = stocks.find_one({"warehouse_id": o["warehouse_id"], "product_id": item["product_id"]})
        if not stock or stock["quantity"] < item["quantity"]:
            orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED"}})
            raise HTTPException(400, f"Insufficient stock for {item['product_name']}")
    
    # Deduct stock
    for item in o["items"]:
        stocks.update_one(
            {"warehouse_id": o["warehouse_id"], "product_id": item["product_id"]},
            {"$inc": {"quantity": -item["quantity"]}}
        )
    
    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "APPROVED", "approved_at": datetime.utcnow()}})
    return {"order_id": order_id, "status": "APPROVED"}

@app.post("/orders/{order_id}/reject")
def reject_order(order_id: str):
    orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "REJECTED", "rejected_at": datetime.utcnow()}})
    return {"order_id": order_id, "status": "REJECTED"}

# ============== RETAILER OPERATIONS ==============
@app.get("/retailers/{retailer_id}/nearby-warehouses")
def get_nearby_warehouses(retailer_id: str):
    r = retailers.find_one({"_id": ObjectId(retailer_id)})
    if not r:
        raise HTTPException(404, "Retailer not found")
    
    nearby = list(warehouses.find({"city": r["city"], "region": r["region"]}, {"name": 1, "address": 1, "city": 1, "region": 1}))
    return {"warehouses": [{"warehouse_id": oid(w["_id"]), **{k:v for k,v in w.items() if k != "_id"}} for w in nearby]}

@app.get("/warehouses/{warehouse_id}/products")
def get_warehouse_products(warehouse_id: str):
    products = list(stocks.find({"warehouse_id": warehouse_id, "quantity": {"$gt": 0}}, {"_id": 0}))
    return {"products": products}

@app.post("/orders")
def place_order(order: OrderCreate):
    # Validate entities exist
    r = retailers.find_one({"_id": ObjectId(order.retailer_id)})
    w = warehouses.find_one({"_id": ObjectId(order.warehouse_id)})
    if not r or not w:
        raise HTTPException(404, "Retailer or Warehouse not found")
    
    doc = order.dict()
    doc["status"] = "PENDING"
    doc["created_at"] = datetime.utcnow()
    res = orders.insert_one(doc)
    return {"order_id": oid(res.inserted_id), "status": "PENDING"}

@app.get("/retailers/{retailer_id}/orders")
def get_retailer_orders(retailer_id: str):
    order_list = list(orders.find({"retailer_id": retailer_id}).sort("created_at", -1))
    for o in order_list:
        o["_id"] = oid(o["_id"])
        o["created_at"] = o["created_at"].isoformat()
    return {"orders": order_list}

# ============== AI/ML FEATURES ==============
@app.post("/warehouses/{warehouse_id}/train-models")
def train_models(warehouse_id: str):
    warehouse_products = list(stocks.find({"warehouse_id": warehouse_id}))
    results = {}
    
    for product in warehouse_products:
        product_id = product["product_id"]
        order_history = list(orders.find({"warehouse_id": warehouse_id, "status": "APPROVED"}))
        
        # Convert orders to sales data
        sales_data = []
        for order in order_history:
            for item in order.get("items", []):
                if item["product_id"] == product_id:
                    sales_data.append({
                        "date": order["created_at"],
                        "product_id": product_id,
                        "quantity": item["quantity"]
                    })
        
        train_result = ml_engine.train_product_model(product_id, sales_data)
        results[product_id] = {"product_name": product["product_name"], **train_result}
    
    return {"training_results": results}

@app.get("/warehouses/{warehouse_id}/restock-predictions")
def get_restock_predictions(warehouse_id: str):
    warehouse_products = list(stocks.find({"warehouse_id": warehouse_id}))
    predictions = []
    
    for product in warehouse_products:
        product_id = product["product_id"]
        current_stock = product["quantity"]
        
        recommendation = ml_engine.get_restock_recommendation(product_id, current_stock)
        
        predictions.append({
            "product_id": product_id,
            "product_name": product["product_name"],
            "current_stock": current_stock,
            "price": product["price"],
            **recommendation
        })
    
    return {"predictions": predictions}

@app.get("/products/{product_id}/demand-forecast")
def get_demand_forecast(product_id: str, days: int = 7):
    forecast = ml_engine.predict_demand(product_id, days)
    forecast_data = []
    base_date = datetime.now()
    
    for i, demand in enumerate(forecast):
        forecast_data.append({
            "date": (base_date + timedelta(days=i+1)).strftime("%Y-%m-%d"),
            "predicted_demand": round(demand, 2)
        })
    
    return {"product_id": product_id, "forecast": forecast_data, "total_predicted_demand": round(sum(forecast), 2)}

# ============== ANALYTICS ==============
@app.get("/analytics/dashboard/{warehouse_id}")
def get_analytics_dashboard(warehouse_id: str):
    total_products = stocks.count_documents({"warehouse_id": warehouse_id})
    total_orders = orders.count_documents({"warehouse_id": warehouse_id})
    pending_orders = orders.count_documents({"warehouse_id": warehouse_id, "status": "PENDING"})
    low_stock = list(stocks.find({"warehouse_id": warehouse_id, "quantity": {"$lt": 10}}, {"_id": 0}))
    
    return {
        "summary": {"total_products": total_products, "total_orders": total_orders, "pending_orders": pending_orders, "low_stock_items": len(low_stock)},
        "low_stock_alerts": low_stock
    }

@app.get("/")
def root():
    return {"message": "Smart Supply Chain API is running!", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Smart Supply Chain API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)  # Disable reload to fix Windows issue