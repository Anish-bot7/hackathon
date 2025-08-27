from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
from sklearn.linear_model import LinearRegression

EARTH_R = 6371.0  # km

def haversine_km(lat1, lon1, lat2, lon2):
    # great-circle distance
    lat1, lon1, lat2, lon2 = map(radians, [lat1,lon1,lat2,lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2*asin(sqrt(a))
    return EARTH_R * c

def nearest_within_km(origin, candidates, radius_km=10.0):
    """origin: (lat,lng), candidates: list[{_id, lat, lng, doc}]"""
    lat, lng = origin
    out = []
    for c in candidates:
        d = haversine_km(lat, lng, c["lat"], c["lng"])
        if d <= radius_km:
            out.append({**c, "distance_km": round(d, 2)})
    # sort by distance
    out.sort(key=lambda x: x["distance_km"])
    return out

def estimate_daily_usage_from_orders(orders: List[Dict]) -> Dict[str, float]:
    """
    Rough estimator: build per-product daily usage from historical orders.
    We aggregate quantity per day and fit simple linear trend; if too few points,
    fallback to mean/day.
    """
    # map product_id -> dict(date->qty)
    per_prod_daily: Dict[str, Dict[datetime, int]] = {}
    for o in orders:
        dt = o["created_at"].date()
        for it in o["items"]:
            pid = it["product_id"]
            per_prod_daily.setdefault(pid, {})
            per_prod_daily[pid][dt] = per_prod_daily[pid].get(dt, 0) + int(it["quantity"])

    usage = {}
    for pid, series in per_prod_daily.items():
        if not series:
            continue
        dates = sorted(series.keys())
        y = np.array([series[d] for d in dates], dtype=float)
        # convert dates to day index
        x = np.array([(d - dates[0]).days for d in dates], dtype=float).reshape(-1,1)
        if len(x) >= 3 and len(set(x.flatten())) >= 2:
            # predicted next-day usage = last intercept + slope * t
            model = LinearRegression().fit(x, y)
            next_t = (dates[-1] - dates[0]).days + 1
            pred = float(model.predict(np.array([[next_t]]))[0])
            # clamp
            usage[pid] = max(0.1, pred)
        else:
            # fallback to average per active day
            days = max(1, (dates[-1] - dates[0]).days + 1)
            usage[pid] = max(0.1, float(sum(y))/days)
    return usage

def predict_days_to_stockout(current_on_hand: Dict[str, int], daily_usage: Dict[str, float]) -> Dict[str, float]:
    out = {}
    for pid, on_hand in current_on_hand.items():
        rate = daily_usage.get(pid, 0.1)
        out[pid] = round(on_hand / max(rate, 0.1), 2)
    return out
