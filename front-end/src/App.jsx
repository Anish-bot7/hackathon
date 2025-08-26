import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import RetailerAuth from "./pages/RetailerAuth";
import WarehouseAuth from "./pages/WarehouseAuth";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/retailer" element={<RetailerAuth />} />
        <Route path="/warehouse" element={<WarehouseAuth />} />
      </Routes>
    </Router>
  );
}
