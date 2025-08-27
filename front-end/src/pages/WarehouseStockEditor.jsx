import React, { useMemo, useState } from "react";
import { upsertWarehouseStock } from "../api";
import { Link } from "react-router-dom";

export default function WarehouseStockEditor() {
  const me = useMemo(() => JSON.parse(localStorage.getItem("warehouse") || "{}"), []);
  const [rows, setRows] = useState([{ product_id:"", product_name:"", quantity:0 }]);

  const addRow = () => setRows([...rows, { product_id:"", product_name:"", quantity:0 }]);
  const update = (i, key, val) => setRows(rows.map((r,idx)=> idx===i ? {...r, [key]: val} : r));
  const save = async () => {
    if (!me?.warehouse_id) return alert("Login as warehouse");
    const cleaned = rows.filter(r => r.product_id && r.product_name && Number(r.quantity));
    if (!cleaned.length) return alert("Add at least one row");
    await upsertWarehouseStock(me.warehouse_id, cleaned);
    alert("Stock updated");
  };

  return (
    <div style={{padding:20}}>
      <p><Link to="/warehouse">← Back</Link></p>
      <h2>Warehouse Stock Editor</h2>
      {rows.map((r,i)=>(
        <div key={i} style={{display:"grid", gridTemplateColumns:"1fr 1fr 120px 100px", gap:8, marginBottom:8}}>
          <input placeholder="product_id" value={r.product_id} onChange={e=>update(i, "product_id", e.target.value)} />
          <input placeholder="product_name" value={r.product_name} onChange={e=>update(i, "product_name", e.target.value)} />
          <input placeholder="quantity" type="number" value={r.quantity} onChange={e=>update(i, "quantity", e.target.value)} />
          <button onClick={addRow}>+</button>
        </div>
      ))}
      <button onClick={save}>Save</button>
    </div>
  );
}
