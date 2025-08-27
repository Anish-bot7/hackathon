import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import RetailerAuth from "./pages/RetailerAuth";
import WarehouseAuth from "./pages/WarehouseAuth";
import RetailerDashboard from "./pages/RetailerDashboard";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/retailer" element={<RetailerAuth />} />
        <Route path="/warehouse" element={<WarehouseAuth />} />
           <Route path="/retailer-dashboard" element={<RetailerDashboard />} />
      </Routes>
    </Router>
  );
}
