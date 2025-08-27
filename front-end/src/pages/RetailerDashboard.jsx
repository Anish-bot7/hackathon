import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  getNearbyWarehouses,
  getWarehouseStock,
  placeOrder,
  getDefaultOrder,
  predictStockout,
} from "../api";
import "./RetailerDashboard.css"; // ✅ External CSS for styling

export default function RetailerDashboard() {
  const me = useMemo(
    () => JSON.parse(localStorage.getItem("retailer") || "{}"),
    []
  );

  const [nearby, setNearby] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [stock, setStock] = useState([]);
  const [cart, setCart] = useState([]);
  const [defaultOrder, setDefaultOrder] = useState([]);
  const [onHand, setOnHand] = useState({});
  const [pred, setPred] = useState(null);
  const [loadingPred, setLoadingPred] = useState(false);

  // ✅ Fetch warehouses + default order
  useEffect(() => {
    if (!me?.retailer_id) return;
    (async () => {
      try {
        const { data } = await getNearbyWarehouses(me.retailer_id, 10);
        setNearby(data?.warehouses || []);
        const d = await getDefaultOrder(me.retailer_id);
        setDefaultOrder(d?.data?.items || []);
        setCart(d?.data?.items || []);
      } catch (err) {
        console.error("Failed fetching initial data:", err);
        alert("Error loading dashboard data.");
      }
    })();
  }, [me]);

  const openWarehouse = async (w) => {
    setSelectedWarehouse(w);
    try {
      const { data } = await getWarehouseStock(w._id);
      setStock(data?.stock || []);
    } catch (err) {
      console.error("Error loading stock:", err);
      alert("Failed to fetch warehouse stock.");
    }
  };

  const addToCart = (p) => {
    const q = Number(prompt(`Enter quantity for ${p.product_name}`, "1"));
    if (!q || q <= 0) return alert("Invalid quantity");

    setCart((prev) => {
      const hit = prev.find((x) => x.product_id === p.product_id);
      if (hit) {
        return prev.map((x) =>
          x.product_id === p.product_id
            ? { ...x, quantity: x.quantity + q }
            : x
        );
      }
      return [
        ...prev,
        { product_id: p.product_id, product_name: p.product_name, quantity: q },
      ];
    });
  };

  const removeFromCart = (pid) => {
    setCart((prev) => prev.filter((item) => item.product_id !== pid));
  };

  const submitOrder = async () => {
    if (!selectedWarehouse) return alert("Pick a warehouse first");
    if (!cart.length) return alert("Cart empty");

    try {
      const { data } = await placeOrder({
        retailer_id: me.retailer_id,
        warehouse_id: selectedWarehouse._id,
        items: cart,
      });
      alert("✅ Order placed successfully! ID: " + data.order_id);
      setCart([]);
    } catch (e) {
      console.error("Order failed:", e);
      alert(e?.response?.data?.detail || "Order failed");
    }
  };

  const runPrediction = async () => {
    setLoadingPred(true);
    try {
      const { data } = await predictStockout(me.retailer_id, onHand);
      setPred(data);
    } catch (err) {
      console.error("Prediction failed:", err);
      alert("Error predicting stockout");
    } finally {
      setLoadingPred(false);
    }
  };

  // 🔹 Lookup function for notifications (map id → product_name)
  const getProductName = (pid) =>
    stock.find((p) => p.product_id === pid)?.product_name ||
    cart.find((c) => c.product_id === pid)?.product_name ||
    defaultOrder.find((d) => d.product_id === pid)?.product_name ||
    pid;

  return (
    <div className="dashboard-container">
      <h2 className="title">📦 Retailer Dashboard</h2>
      <p className="subtitle">
        <b>{me?.name || "Retailer"}</b> — {me?.location_name || "Unknown"}
      </p>

      {/* Warehouses */}
      <section className="card">
        <h3>Nearby Warehouses (within 10 km)</h3>
        {nearby.length ? (
          <ul className="list">
            {nearby.map((w) => (
              <li key={w._id}>
                <button className="btn" onClick={() => openWarehouse(w)}>
                  {w.name} — {w.location_name} ({w.distance_km} km)
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No warehouses nearby.</p>
        )}
      </section>

      {/* Stock */}
      {selectedWarehouse && (
        <section className="card">
          <h3>Stock at {selectedWarehouse.name}</h3>
          {stock.length ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Available Qty</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {stock.map((p) => (
                  <tr key={p.product_id}>
                    <td>{p.product_name}</td>
                    <td>{p.quantity}</td>
                    <td>
                      <button
                        className="btn small"
                        onClick={() => addToCart(p)}
                      >
                        ➕ Add
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No stock available here.</p>
          )}
        </section>
      )}

      {/* Default Order */}
      <section className="card">
        <h3>Default Order</h3>
        {defaultOrder.length ? (
          <ul className="list">
            {defaultOrder.map((item, idx) => (
              <li key={idx}>
                {item.product_name} — <b>{item.quantity}</b>
              </li>
            ))}
          </ul>
        ) : (
          <p>No default order found.</p>
        )}
      </section>

      {/* Cart */}
      <section className="card">
        <h3>🛒 Cart</h3>
        {cart.length ? (
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((c, i) => (
                <tr key={i}>
                  <td>{c.product_name}</td>
                  <td>{c.quantity}</td>
                  <td>
                    <button
                      className="btn danger small"
                      onClick={() => removeFromCart(c.product_id)}
                    >
                      ❌ Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>Cart is empty.</p>
        )}
        <button className="btn primary" onClick={submitOrder}>
          🚀 Place Order
        </button>
      </section>

      {/* Prediction */}
      <section className="card">
        <h3>🔮 Predict Stock Finish Time (ML)</h3>
        <p>Enter your current on-hand inventory (approx):</p>
        <OnHandEditor onHand={onHand} setOnHand={setOnHand} />
        <button
          className="btn primary"
          onClick={runPrediction}
          disabled={loadingPred}
        >
          {loadingPred ? "Predicting..." : "Predict"}
        </button>

        {pred && (
          <div className="prediction-box">
            <h4>Daily Usage (estimated)</h4>
            <pre>{JSON.stringify(pred.daily_usage, null, 2)}</pre>
            <h4>Days to Stockout</h4>
            <pre>{JSON.stringify(pred.days_to_stockout, null, 2)}</pre>
            {pred.notifications?.length ? (
              <>
                <h4>Notifications</h4>
                <ul>
                  {pred.notifications.map((n, i) => (
                    <li key={i}>
                      {getProductName(n.product_id)}: {n.message}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}

// ✅ OnHand Editor
function OnHandEditor({ onHand, setOnHand }) {
  const [pid, setPid] = useState("");
  const [qty, setQty] = useState("");

  const add = useCallback(() => {
    if (!pid || !qty || Number(qty) <= 0) {
      alert("Invalid product or quantity");
      return;
    }
    setOnHand((prev) => ({ ...prev, [pid]: Number(qty) }));
    setPid("");
    setQty("");
  }, [pid, qty, setOnHand]);

  return (
    <div className="onhand-editor">
      <input
        placeholder="product_id"
        value={pid}
        onChange={(e) => setPid(e.target.value)}
      />
      <input
        placeholder="on hand qty"
        type="number"
        value={qty}
        onChange={(e) => setQty(e.target.value)}
      />
      <button className="btn small" onClick={add}>
        Add/Update
      </button>
      <pre>{JSON.stringify(onHand, null, 2)}</pre>
    </div>
  );
}
