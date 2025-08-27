import React, { useState } from "react";
import "./Login.css";
import { FaUser, FaLock, FaMapMarkerAlt } from "react-icons/fa";

export default function WarehouseAuth() {
  const [isLogin, setIsLogin] = useState(true);
  const [ownerName, setOwnerName] = useState("");
  const [location, setLocation] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    const endpoint = isLogin
      ? "http://127.0.0.1:8000/login/warehouse"
      : "http://127.0.0.1:8000/register/warehouse";

    const payload = isLogin
      ? { owner_name: ownerName, password }
      : { owner_name: ownerName, location, password };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.detail || "Something went wrong");
      } else {
       alert(data.msg);
      }
    } catch (err) {
      setMessage("❌ Server error. Check if backend is running.");
    }
  };

  return (
    <div className="login-container">
      {/* Navbar */}
      <nav className="login-navbar">
        <h1>Smart Supply Chain - Warehouse</h1>
      </nav>

      <main className="login-main">
        <div className="login-card">
          <h2>{isLogin ? "Warehouse Login" : "Warehouse Registration"}</h2>
          <p className="mb-6 text-gray-700 text-center">
            {isLogin
              ? "Enter your owner name and password to login"
              : "Fill details to register as a warehouse"}
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
                  required
                  className="outline-none w-full"
                />
              </div>
            )}

            <div className="flex items-center gap-2 border rounded-md px-3 py-2">
              <FaUser />
              <input
                type="text"
                placeholder="Owner Name"
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
                required
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
                required
                className="outline-none w-full"
              />
            </div>

            <button type="submit" className="login-btn warehouse mt-2">
              {isLogin ? "Login" : "Register"}
            </button>
          </form>

          {message && <p className="mt-4 text-center">{message}</p>}

          <p
            className="mt-4 text-center text-sm text-green-700 cursor-pointer"
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
