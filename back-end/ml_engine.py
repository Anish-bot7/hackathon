import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

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
        if len(X) > 10:
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            model.fit(X_train, y_train)
            
            if len(X_test) > 0:
                pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, pred)
            else:
                mae = 0
        else:
            model.fit(X, y)
            mae = 0
        
        # Store model
        self.models[product_id] = {
            "model": model,
            "model_type": model_type,
            "feature_cols": feature_cols,
            "last_data": df_clean.iloc[-1].to_dict(),
            "mae": mae,
            "avg_demand": np.mean(y),
            "volatility": volatility
        }
        
        return {"status": "success", "model_type": model_type, "mae": round(mae, 2), "data_points": len(sales_data)}
    
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
            
            # Update moving averages
            if 'ma_3' in last_data:
                last_data['ma_3'] = (last_data.get('lag_1', pred) + last_data.get('lag_2', pred) + last_data.get('lag_3', pred)) / 3
            if 'ma_7' in last_data:
                recent_lags = [last_data.get(f'lag_{i}', pred) for i in range(1, 8)]
                last_data['ma_7'] = np.mean(recent_lags)
                last_data['std_7'] = np.std(recent_lags)
        
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
        model_info = self.models.get(product_id, {})
        data_points = model_info.get("mae", 999)
        
        if data_points < 2 and product_id in self.models:
            confidence = "HIGH"
        elif data_points < 5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
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
    
    def predict_stockout(self, retailer_id: str, current_stock: Dict[str, int]) -> Dict:
        """Predict stockout times for retailer's current stock"""
        daily_usage = {}
        days_to_stockout = {}
        notifications = []
        
        for product_id, stock_qty in current_stock.items():
            # Get average daily demand
            if product_id in self.models:
                forecast = self.predict_demand(product_id, 7)
                avg_demand = np.mean(forecast)
            else:
                avg_demand = 1.0  # Default
            
            daily_usage[product_id] = round(avg_demand, 2)
            
            # Calculate days to stockout
            if avg_demand <= 0:
                days_left = 999.0
            else:
                days_left = max(0, stock_qty / avg_demand)
            
            days_to_stockout[product_id] = round(days_left, 1)
            
            # Generate notifications
            if days_left < 3:
                notifications.append({
                    "product_id": product_id,
                    "message": f"URGENT: Stock will finish in {days_left:.1f} days",
                    "priority": "HIGH"
                })
            elif days_left < 7:
                notifications.append({
                    "product_id": product_id,
                    "message": f"WARNING: Stock will finish in {days_left:.1f} days",
                    "priority": "MEDIUM"
                })
        
        return {
            "daily_usage": daily_usage,
            "days_to_stockout": days_to_stockout,
            "notifications": notifications
        }