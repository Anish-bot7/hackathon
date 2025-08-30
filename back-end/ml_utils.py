import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

class SupplyChainML:
    def __init__(self):
        self.models = {}
        self.min_data_points = 14  # Minimum days of data needed
        self.switch_to_rl_threshold = 100  # Switch to deep RL after 100 data points
        
    def prepare_features(self, sales_data: pd.DataFrame) -> tuple:
        """Prepare features for linear regression model"""
        df = sales_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_num'] = (df['date'] - df['date'].min()).dt.days
        
        # Lag features
        for i in range(1, min(8, len(df))):
            df[f'lag_{i}'] = df['quantity'].shift(i)
        
        # Rolling averages
        df['ma_3'] = df['quantity'].rolling(3).mean()
        df['ma_7'] = df['quantity'].rolling(7).mean()
        
        # Drop rows with NaN values
        df = df.dropna()
        
        if len(df) == 0:
            return None, None, None
            
        feature_cols = [col for col in df.columns if col not in ['date', 'quantity', 'product_id', 'retailer_id']]
        X = df[feature_cols]
        y = df['quantity']
        
        return X, y, df
    
    def train_model(self, product_id: str, sales_data: List[Dict]) -> Dict[str, Any]:
        """Train prediction model for a product"""
        if len(sales_data) < self.min_data_points:
            return {"status": "insufficient_data", "model_type": None}
        
        df = pd.DataFrame(sales_data)
        X, y, processed_df = self.prepare_features(df)
        
        if X is None or len(X) < 5:
            return {"status": "insufficient_features", "model_type": None}
        
        # Use Linear Regression for now (will switch to Deep RL later)
        model = LinearRegression()
        
        # Split data for validation
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        model.fit(X_train, y_train)
        
        # Calculate error if we have test data
        mae = None
        if len(X_test) > 0:
            pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, pred)
        
        self.models[product_id] = {
            "model": model,
            "model_type": "linear_regression",
            "last_data": processed_df.iloc[-1].to_dict(),
            "mae": mae,
            "data_points": len(sales_data)
        }
        
        return {
            "status": "success",
            "model_type": "linear_regression",
            "mae": mae,
            "data_points": len(sales_data)
        }
    
    def predict_daily_demand(self, product_id: str, days: int = 7) -> List[float]:
        """Predict daily demand for next N days"""
        if product_id not in self.models:
            return [0.0] * days
        
        model_info = self.models[product_id]
        model = model_info["model"]
        last_data = model_info["last_data"]
        
        predictions = []
        current_features = last_data.copy()
        
        for day in range(days):
            # Prepare feature vector
            feature_cols = [col for col in current_features.keys() 
                          if col not in ['date', 'quantity', 'product_id', 'retailer_id']]
            X_pred = np.array([current_features[col] for col in feature_cols]).reshape(1, -1)
            
            # Make prediction
            pred = max(0, model.predict(X_pred)[0])
            predictions.append(pred)
            
            # Update features for next prediction
            current_features['day_num'] += 1
            current_features['day_of_week'] = (current_features['day_of_week'] + 1) % 7
            
            # Update lag features
            for i in range(7, 1, -1):
                if f'lag_{i}' in current_features:
                    current_features[f'lag_{i}'] = current_features.get(f'lag_{i-1}', pred)
            current_features['lag_1'] = pred
            
            # Update moving averages (simplified)
            if 'ma_3' in current_features:
                current_features['ma_3'] = pred  # Simplified
            if 'ma_7' in current_features:
                current_features['ma_7'] = pred  # Simplified
        
        return predictions

def estimate_daily_usage_from_orders(order_history: List[Dict]) -> Dict[str, float]:
    """Estimate daily usage per product from order history"""
    if not order_history:
        return {}
    
    df = pd.DataFrame(order_history)
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Group by product and calculate total quantity over time period
    usage = df.groupby('product_id')['quantity'].sum()
    
    # Calculate date range
    date_range = (df['created_at'].max() - df['created_at'].min()).days
    if date_range == 0:
        date_range = 1
    
    # Calculate daily usage
    daily_usage = {}
    for product_id, total_qty in usage.items():
        daily_usage[str(product_id)] = total_qty / date_range
    
    return daily_usage

def predict_days_to_stockout(current_stock: Dict[str, int], daily_usage: Dict[str, float]) -> Dict[str, float]:
    """Predict days until stockout for each product"""
    days_left = {}
    
    for product_id, stock_qty in current_stock.items():
        usage_rate = daily_usage.get(str(product_id), 0.5)  # Default to 0.5 if no history
        if usage_rate <= 0:
            days_left[product_id] = 999.0  # Very high number for no usage
        else:
            days_left[product_id] = max(0, stock_qty / usage_rate)
    
    return days_left

def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int, safety_factor: float = 1.5) -> int:
    """Calculate reorder point using simple formula"""
    safety_stock = safety_factor * avg_daily_demand * np.sqrt(lead_time_days)
    reorder_point = avg_daily_demand * lead_time_days + safety_stock
    return max(1, int(np.ceil(reorder_point)))

def calculate_optimal_order_quantity(daily_demand: float, lead_time: int, review_period: int = 7) -> int:
    """Calculate optimal order quantity"""
    demand_during_lead_and_review = daily_demand * (lead_time + review_period)
    return max(1, int(np.ceil(demand_during_lead_and_review * 1.2)))