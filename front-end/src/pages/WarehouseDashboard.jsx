// src/pages/Warehouse/Dashboard.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard({ ownerName }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    // (Optional) clear any auth tokens from localStorage/sessionStorage
    localStorage.removeItem("warehouseOwner");

    // Redirect to Warehouse Login page
    navigate("/warehouse");
  };

  return (
    <div className="dashboard">
      {/* Navbar */}
      <nav className="dashboard-navbar">
        <h1>Smart Supply Chain</h1>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </nav>

      <main className="dashboard-main">
        <h2>Welcome, {ownerName} 👋</h2>
        <section className="orders-section">
          <h3>📦 My Orders</h3>
          <p>Here you will see orders from retailers to this warehouse.</p>
        </section>

        <section className="restock-section">
          <h3>🔄 Restock Details</h3>
          <p>Shows which items are in stock and which need restocking.</p>
        </section>
      </main>
    </div>
  );
}
