import React from "react";
import "./Login.css";
import { FaStore, FaWarehouse, FaTwitter, FaLinkedin, FaInstagram, FaEnvelope } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  return (
    <div className="login-container">
      {/* Navbar */}
      <nav className="login-navbar">
        <h1>Smart Supply Chain</h1>
      </nav>

      {/* Main Login Section */}
      <main className="login-main">
        <div className="login-card">
          <h2>Welcome Back</h2>
          <p className="mb-6 text-gray-700 text-center">Login as Retailer or Warehouse</p>

          <div className="flex flex-row gap-6 justify-center items-center mt-6">
            <button
              className="login-btn retailer"
              onClick={() => navigate("/retailer")}
            >
              <FaStore size={20} /> Retailer
            </button>
            <button
              className="login-btn warehouse"
              onClick={() => navigate("/warehouse")}
            >
              <FaWarehouse size={20} /> Warehouse
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="login-footer">
        <p>© 2025 Smart Supply Chain. All rights reserved.</p>
        <div className="socials">
          <a href="#"><FaTwitter /></a>
          <a href="#"><FaLinkedin /></a>
          <a href="#"><FaInstagram /></a>
          <a href="mailto:support@supplychain.com"><FaEnvelope /></a>
        </div>
      </footer>
    </div>
  );
}
