#!pip -q install xgboost==2.0.3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

np.random.seed(42)
# Sample products i created.Should make it as adding products using the website
products = [
    {"product_id": 201, "name": "Maggi", "shelf_life_days": 180},
    {"product_id": 202, "name": "Milk",  "shelf_life_days": 7},
]

manufacturers = pd.DataFrame([
    {"manufacturer_id": "M1", "product_id": 201, "unit_price": 10.5, "lead_time_days": 3},
    {"manufacturer_id": "M2", "product_id": 201, "unit_price": 10.0, "lead_time_days": 4},
    {"manufacturer_id": "M3", "product_id": 201, "unit_price": 11.0, "lead_time_days": 2},
    {"manufacturer_id": "M1", "product_id": 202, "unit_price": 24.0, "lead_time_days": 2},
    {"manufacturer_id": "M2", "product_id": 202, "unit_price": 23.5, "lead_time_days": 3},
    {"manufacturer_id": "M3", "product_id": 202, "unit_price": 25.0, "lead_time_days": 1},
])

retailer_state = pd.DataFrame([
    {"product_id": 201, "current_stock": 10},
    {"product_id": 202, "current_stock": 20},
])


def make_sales_series(base, trend=0.02, season_amp=0.15, days=90):
    t = np.arange(days)
    season = 1 + season_amp * np.sin(2 * np.pi * t / 7)
    noise = np.random.normal(0, 0.1, size=days)
    series = base * (1 + trend * (t / days)) * season * (1 + noise)
    return np.maximum(0, np.round(series)).astype(int)

sales_history = []
start_date = datetime(2025, 5, 29)
for p in products:
    if p["name"] == "Maggi":
        base = 14
    else:
        base = 26
    s = make_sales_series(base=base, days=90)
    for i, qty in enumerate(s):
        sales_history.append({
            "date": start_date + timedelta(days=i),
            "product_id": p["product_id"],
            "sales": int(qty)
        })
sales_df = pd.DataFrame(sales_history)

today = sales_df["date"].max()
print(f"Data covers up to: {today.date()}")


def build_supervised(df_prod: pd.DataFrame, lags=7):
    df = df_prod.sort_values("date").copy()
    df["dow"] = df["date"].dt.dayofweek
    for i in range(lags):
        df[f"lag_{i+1}"] = df["sales"].shift(i+1)
    df["ma_7"] = df["sales"].rolling(7).mean()
    df["std_7"] = df["sales"].rolling(7).std().fillna(0)
    dow_oh = pd.get_dummies(df["dow"], prefix="dow")
    df = pd.concat([df, dow_oh], axis=1)
    df = df.dropna().reset_index(drop=True)
    X = df.drop(columns=["sales", "date"])
    y = df["sales"]
    return X, y, df

models = {}
metrics = {}
for p in products:
    pid = p["product_id"]
    dfp = sales_df[sales_df["product_id"] == pid].copy()
    X, y, df_sup = build_supervised(dfp)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = XGBRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    models[pid] = model
    metrics[pid] = mae

print("Validation MAE by product:", metrics)

#Prediction of sales
def forecast_next_7_days(pid: int):
    dfp = sales_df[sales_df["product_id"] == pid].copy().sort_values("date")
    last_date = dfp["date"].max()
    model = models[pid]

    X_all, _, df_sup = build_supervised(dfp)
    last_row = df_sup.iloc[-1:].copy()
    future = []
    lag_cols = [c for c in last_row.columns if c.startswith("lag_")]
    for step in range(1, 8):
        next_date = last_date + timedelta(days=step)
        dow = next_date.weekday()
        dow_cols = [c for c in last_row.columns if c.startswith("dow_")]
        for c in dow_cols:
            last_row[c] = 0
        last_row[f"dow_{dow}"] = 1
        X_pred = last_row.drop(columns=["date", "sales"], errors="ignore")
        y_hat = float(model.predict(X_pred)[0])
        y_hat = max(0, y_hat)
        future.append({"date": next_date.date(), "product_id": pid, "forecast": y_hat})
        prev_lags = [last_row[f"lag_{i+1}"].iloc[0] for i in range(len(lag_cols))]
        new_lags = [y_hat] + prev_lags[:-1]
        for i, val in enumerate(new_lags, start=1):
            last_row[f"lag_{i}"] = val
        last_row["ma_7"] = np.mean([last_row[f"lag_{i}"].iloc[0] for i in range(1, 8)])
        last_row["std_7"] = np.std([last_row[f"lag_{i}"].iloc[0] for i in range(1, 8)])

    return pd.DataFrame(future)

forecasts = []
for p in products:
    forecasts.append(forecast_next_7_days(p["product_id"]))
forecast_df = pd.concat(forecasts, ignore_index=True)

print("\n7-day forecast (head):")
print(forecast_df.head())
#
def reorder_plan_for_retailer(pid: int,
                              current_stock: int,
                              lead_time_days: int,
                              service_factor: float = 1.28,
                              review_period_days: int = 7):
    f = forecast_df[forecast_df["product_id"] == pid].copy()
    demand_lt = f.iloc[:lead_time_days]["forecast"].sum() if lead_time_days > 0 else 0.0
    std_daily = f["forecast"].std() if len(f) > 1 else 0.0
    std_lt = std_daily * np.sqrt(max(1, lead_time_days))
    safety = service_factor * std_lt

    rop = demand_lt + safety
    days_until_reorder = 0
    proj_stock = float(current_stock)
    for i, row in f.iterrows():
        if proj_stock <= rop:
            break
        proj_stock -= row["forecast"]
        days_until_reorder += 1

    reorder_date = (today + timedelta(days=days_until_reorder)).date()

    demand_review = f.iloc[:lead_time_days + review_period_days]["forecast"].sum()
    order_qty = max(0.0, demand_review + safety - current_stock)

    return {
        "rop": round(float(rop), 2),
        "safety_stock": round(float(safety), 2),
        "reorder_date": str(reorder_date),
        "suggested_order_qty": int(np.ceil(order_qty))
    }
def choose_best_manufacturer(pid: int, lead_time_penalty_per_day: float = 0.0):
    options = manufacturers[manufacturers["product_id"] == pid].copy()
    options["effective_cost"] = options["unit_price"] + lead_time_penalty_per_day * options["lead_time_days"]
    best = options.sort_values(["effective_cost", "lead_time_days"]).iloc[0]
    return {
        "manufacturer_id": best["manufacturer_id"],
        "unit_price": float(best["unit_price"]),
        "lead_time_days": int(best["lead_time_days"]),
        "effective_cost": float(best["effective_cost"])
    }


orders_table = []

def recommend_for_retailer(auto_order: bool = False, lead_time_penalty_per_day: float = 0.0):
    recs = []
    for _, r in retailer_state.iterrows():
        pid = int(r["product_id"])
        current_stock = int(r["current_stock"])
        best_manu = choose_best_manufacturer(pid, lead_time_penalty_per_day)
        plan = reorder_plan_for_retailer(
            pid=pid,
            current_stock=current_stock,
            lead_time_days=best_manu["lead_time_days"],
        )
        prod_name = [p["name"] for p in products if p["product_id"] == pid][0]
        rec = {
            "product_id": pid,
            "product_name": prod_name,
            "current_stock": current_stock,
            "best_manufacturer": best_manu["manufacturer_id"],
            "unit_price": best_manu["unit_price"],
            "lead_time_days": best_manu["lead_time_days"],
            "effective_cost": round(best_manu["effective_cost"], 2),
            "rop": plan["rop"],
            "safety_stock": plan["safety_stock"],
            "suggested_reorder_date": plan["reorder_date"],
            "suggested_order_qty": plan["suggested_order_qty"]
        }
        recs.append(rec)

        if auto_order and rec["suggested_order_qty"] > 0:
            eta = (today + timedelta(days=rec["lead_time_days"])).date()
            orders_table.append({
                "created_at": str(today.date()),
                "product_id": pid,
                "product_name": prod_name,
                "manufacturer_id": rec["best_manufacturer"],
                "order_qty": rec["suggested_order_qty"],
                "eta": str(eta),
                "unit_price": rec["unit_price"],
                "total_value": round(rec["unit_price"] * rec["suggested_order_qty"], 2)
            })
    return pd.DataFrame(recs)
def manufacturer_restock_plan(retailer_recs: pd.DataFrame, safety_factor: float = 0.1):
    if retailer_recs.empty:
        return pd.DataFrame(columns=["manufacturer_id","product_id","product_name","incoming_qty","suggested_restock_qty"])
    rows = []
    for _, rec in retailer_recs.iterrows():
        rows.append({
            "manufacturer_id": rec["best_manufacturer"],
            "product_id": rec["product_id"],
            "product_name": rec["product_name"],
            "incoming_qty": int(rec["suggested_order_qty"])
        })
    agg = pd.DataFrame(rows).groupby(["manufacturer_id","product_id","product_name"], as_index=False).sum()
    agg["suggested_restock_qty"] = (agg["incoming_qty"] * (1 + safety_factor)).astype(int)
    return agg
retailer_recs = recommend_for_retailer(auto_order=False, lead_time_penalty_per_day=0.2)
print("\nRetailer recommendations (no auto-order):")
display(retailer_recs)


orders_table.clear()
retailer_recs_auto = recommend_for_retailer(auto_order=True, lead_time_penalty_per_day=0.2)
print("\nRetailer recommendations (auto-order ON):")
display(retailer_recs_auto)

print("\nAuto-created orders:")
display(pd.DataFrame(orders_table))
mfg_plan = manufacturer_restock_plan(retailer_recs_auto, safety_factor=0.15)
print("\nManufacturer restock plan (aggregated):")
display(mfg_plan)
