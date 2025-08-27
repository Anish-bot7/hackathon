import React, { useState } from "react";
import "./Login.css";
import { FaLock, FaMapMarkerAlt, FaStore } from "react-icons/fa";
import { registerRetailer, loginRetailer } from "../api";
import { useNavigate } from "react-router-dom";  // ✅ Import navigate

export default function RetailerAuth() {
  const [isLogin, setIsLogin] = useState(true);
  const [shopName, setShopName] = useState("");
  const [location, setLocation] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate(); // ✅ Initialize navigation

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (isLogin) {
        // ✅ Login API call
        const res = await loginRetailer({
          shop_name: shopName,
          password,
        });
        alert(res.data.msg); // e.g., "Retailer login successful"

        // ✅ Redirect to Retailer Dashboard
        navigate("/retailer-dashboard");
      } else {
        // ✅ Register API call
        const res = await registerRetailer({
          shop_name: shopName,
          location,
          password,
        });
        alert(res.data.msg); // e.g., "Retailer registered successfully"
        setIsLogin(true); // switch to login after registration
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Something went wrong");
    }
  };

  return (
    <div className="login-container">
      {/* Navbar */}
      <nav className="login-navbar">
        <h1>Smart Supply Chain - Retailer</h1>
      </nav>

      <main className="login-main">
        <div className="login-card">
          <h2>{isLogin ? "Retailer Login" : "Retailer Registration"}</h2>
          <p className="mb-6 text-gray-700 text-center">
            {isLogin
              ? "Enter your shop name and password to login"
              : "Fill details to register as a retailer"}
          </p>

          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="flex items-center gap-2 border rounded-md px-3 py-2">
                <FaMapMarkerAlt />
                <input
                  type="text"
                  placeholder="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="outline-none w-full"
                />
              </div>
            )}

            <div className="flex items-center gap-2 border rounded-md px-3 py-2">
              <FaStore />
              <input
                type="text"
                placeholder="Shop Name"
                value={shopName}
                onChange={(e) => setShopName(e.target.value)}
                className="outline-none w-full"
              />
            </div>

            <div className="flex items-center gap-2 border rounded-md px-3 py-2">
              <FaLock />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="outline-none w-full"
              />
            </div>

            <button type="submit" className="login-btn retailer mt-2">
              {isLogin ? "Login" : "Register"}
            </button>
          </form>

          <p
            className="mt-4 text-center text-sm text-blue-700 cursor-pointer"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin
              ? "Don't have an account? Register"
              : "Already have an account? Login"}
          </p>
        </div>
      </main>
    </div>
  );
}
