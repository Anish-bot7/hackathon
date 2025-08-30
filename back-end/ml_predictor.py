import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

class SmartInventoryPredictor:
    def _init_(self):
        self.models = {}
        self.product_stats = {}
        self.min_linear_data = 14
        self.min_advanced_data = 50
        
    def analyze_product_pattern(self, sales_data: pd.DataFrame) -> Dict:
        """Analyze sales pattern to choose best model"""
        if len(sales_data) < 7:
            return {"pattern": "insufficient_data", "volatility": "unknown"}
        
        daily_sales = sales_data['quantity'].values
        
        # Calculate volatility
        cv = np.std(daily_sales) / np.mean(daily_sales) if np.mean(daily_sales) > 0 else 0
        
        # Detect seasonality (weekly pattern)
        if len(daily_sales) >= 14:
            weekly_corr = np.corrcoef(daily_sales[:-7], daily_sales[7:])[0, 1]
            weekly_corr = 0 if np.isnan(weekly_corr) else weekly_corr
        else:
            weekly_corr = 0
        
        # Classify pattern
        if cv < 0.3:
            pattern = "stable"
        elif cv < 0.6:
            pattern = "moderate"
        else:
            pattern = "volatile"
        
        return {
            "pattern": pattern,
            "volatility": cv,
            "weekly_seasonality": weekly_corr,
            "avg_daily_sales": np.mean(daily_sales)
        }
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML model"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Time features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Lag features
        max_lags = min(7, len(df) // 2)
        for i in range(1, max_lags + 1):
            df[f'lag_{i}'] = df['quantity'].shift(i)
        
        # Rolling statistics
        df['ma_3'] = df['quantity'].rolling(3, min_periods=1).mean()
        df['ma_7'] = df['quantity'].rolling(7, min_periods=1).mean()
        df['std_3'] = df['quantity'].rolling(3, min_periods=1).std().fillna(0)
        
        # Trend
        df['trend'] = np.arange(len(df))
        
        return df
    
    def train_product_model(self, product_id: str, sales_data: List[Dict]) -> Dict:
        """Train model for specific product"""
        if len(sales_data) < self.min_linear_data:
            return {"status": "insufficient_data", "model_type": None}
        
        # Convert to DataFrame
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Analyze pattern
        stats = self.analyze_product_pattern(df)
        self.product_stats[product_id] = stats
        
        # Create features
        df_features = self.create_features(df)
        df_clean = df_features.dropna()
        
        if len(df_clean) < 5:
            return {"status": "insufficient_clean_data", "model_type": None}
        
        # Prepare training data
        feature_cols = [col for col in df_clean.columns 
                       if col not in ['date', 'quantity', 'product_id', 'retailer_id']]
        X = df_clean[feature_cols]
        y = df_clean['quantity']
        
        # Choose model based on data size and pattern
        if len(sales_data) >= self.min_advanced_data and stats['volatility'] > 0.4:
            model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
            model_type = "random_forest"
        else:
            model = LinearRegression()
            model_type = "linear_regression"
        
        # Train model
        model.fit(X, y)
        
        # Store model and metadata
        self.models[product_id] = {
            "model": model,
            "model_type": model_type,
            "feature_cols": feature_cols,
            "last_features": df_clean.iloc[-1],
            "stats": stats,
            "trained_at": datetime.now()
        }
        
        return {
            "status": "success",
            "model_type": model_type,
            "data_points": len(sales_data),
            "pattern": stats['pattern']
        }
    
    def predict_demand(self, product_id: str, days_ahead: int = 7) -> List[float]:
        """Predict demand for next N days"""
        if product_id not in self.models:
            # Fallback to simple average if no model
            stats = self.product_stats.get(product_id, {"avg_daily_sales": 1.0})
            avg = stats.get("avg_daily_sales", 1.0)
            return [max(0, avg + np.random.normal(0, 0.1)) for _ in range(days_ahead)]
        
        model_info = self.models[product_id]
        model = model_info["model"]
        feature_cols = model_info["feature_cols"]
        last_features = model_info["last_features"].copy()
        
        predictions = []
        
        for day in range(days_ahead):
            # Prepare current features
            X_pred = np.array([last_features[col] for col in feature_cols]).reshape(1, -1)
            
            # Make prediction
            pred = max(0, model.predict(X_pred)[0])
            predictions.append(pred)
            
            # Update features for next iteration
            last_features['trend'] += 1
            last_features['day_of_week'] = (last_features['day_of_week'] + 1) % 7
            last_features['is_weekend'] = 1 if last_features['day_of_week'] >= 5 else 0
            
            # Update lag features
            for i in range(7, 1, -1):
                if f'lag_{i}' in last_features:
                    last_features[f'lag_{i}'] = last_features.get(f'lag_{i-1}', pred)
            if 'lag_1' in last_features:
                last_features['lag_1'] = pred
            
            # Update moving averages (simplified)
            if 'ma_3' in last_features:
                last_features['ma_3'] = pred
            if 'ma_7' in last_features:
                last_features['ma_7'] = pred
        
        return predictions
    
    def calculate_restock_recommendation(self, 
                                       product_id: str,
                                       current_stock: int,
                                       lead_time_days: int = 3,
                                       service_level: float = 0.95) -> Dict:
        """Calculate when and how much to restock"""
        
        # Predict demand for lead time + review period
        forecast_days = lead_time_days + 7  # 7-day review period
        demand_forecast = self.predict_demand(product_id, forecast_days)
        
        # Calculate statistics
        total_demand = sum(demand_forecast)
        avg_daily_demand = np.mean(demand_forecast)
        demand_std = np.std(demand_forecast) if len(demand_forecast) > 1 else avg_daily_demand * 0.2
        
        # Safety stock calculation
        z_score = 1.96 if service_level >= 0.95 else 1.28  # 95% vs 90% service level
        safety_stock = z_score * demand_std * np.sqrt(lead_time_days)
        
        # Reorder point
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
        
        # Confidence level based on model performance and data
        model_info = self.models.get(product_id, {})
        data_points = model_info.get("stats", {}).get("avg_daily_sales", 0)
        
        if data_points >= 50:
            confidence = "HIGH"
        elif data_points >= 20:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        reorder_date = datetime.now() + timedelta(days=days_to_reorder)
        
        return {
            "reorder_point": round(reorder_point, 2),
            "safety_stock": round(safety_stock, 2),
            "days_to_reorder": days_to_reorder,
            "reorder_date": reorder_date.strftime("%Y-%m-%d"),
            "suggested_order_qty": int(np.ceil(order_qty)),
            "confidence_level": confidence,
            "avg_daily_demand": round(avg_daily_demand, 2)
        }

# Global ML instance
ml_engine = SmartInventoryPredictor()

def get_sales_from_orders(orders: List[Dict]) -> List[Dict]:
    """Convert orders to sales records for ML training"""
    sales_records = []
    for order in orders:
        if order.get('status') == 'APPROVED':
            sales_records.append({
                "date": order['created_at'],
                "product_id": order['product_id'],
                "quantity": order['quantity'],
                "retailer_id": order.get('retailer_id')
            })
    return sales_records