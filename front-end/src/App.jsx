import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import RetailerAuth from "./pages/RetailerAuth";
import RetailerDashboard from "./pages/RetailerDashboard";
import WarehouseDashboard from "./pages/WarehouseDashboard";
import WarehouseStockEditor from "./pages/WarehouseStockEditor";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RetailerAuth />} />
        <Route path="/retailer" element={<RetailerDashboard />} />
        <Route path="/warehouse" element={<WarehouseDashboard />} />
        <Route path="/warehouse/stock" element={<WarehouseStockEditor />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
