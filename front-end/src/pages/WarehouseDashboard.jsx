import React, { useEffect, useMemo, useState } from "react";
import { getWarehouseOrders } from "../api";
import { Link } from "react-router-dom";

export default function WarehouseDashboard() {
  const me = useMemo(() => JSON.parse(localStorage.getItem("warehouse") || "{}"), []);
  const [orders, setOrders] = useState([]);

  useEffect(()=>{
    if (!me?.warehouse_id) return;
    (async()=>{
      const { data } = await getWarehouseOrders(me.warehouse_id);
      setOrders(data.orders || []);
    })();
  }, [me]);

  return (
    <div style={{padding:20}}>
      <h2>Warehouse Dashboard</h2>
      <p><b>{me?.name}</b> — {me?.location_name}</p>
      <p><Link to="/warehouse/stock">Manage Stock</Link></p>

      <h3>Incoming Orders</h3>
      <ul>
        {orders.map(o=>(
          <li key={o.order_id}>
            #{o.order_id.slice(-6)} — Retailer: {o.retailer_id} — Items: {o.items.length} — Status: {o.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
