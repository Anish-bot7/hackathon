import React, { useState } from "react";
import "./Login.css";
import { FaUser, FaLock, FaMapMarkerAlt, FaWarehouse } from "react-icons/fa";

export default function WarehouseAuth() {
  const [isLogin, setIsLogin] = useState(true);

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

          <form className="flex flex-col gap-4">
            {!isLogin && (
              <>
                <div className="flex items-center gap-2 border rounded-md px-3 py-2">
                  <FaMapMarkerAlt />
                  <input
                    type="text"
                    placeholder="Location"
                    className="outline-none w-full"
                  />
                </div>
                <div className="flex items-center gap-2 border rounded-md px-3 py-2">
                  <FaUser />
                  <input
                    type="text"
                    placeholder="Owner Name"
                    className="outline-none w-full"
                  />
                </div>
              </>
            )}

            {isLogin && (
              <div className="flex items-center gap-2 border rounded-md px-3 py-2">
                <FaUser />
                <input
                  type="text"
                  placeholder="Owner Name"
                  className="outline-none w-full"
                />
              </div>
            )}

            <div className="flex items-center gap-2 border rounded-md px-3 py-2">
              <FaLock />
              <input
                type="password"
                placeholder="Password"
                className="outline-none w-full"
              />
            </div>

            <button
              type="submit"
              className="login-btn warehouse mt-2"
            >
              {isLogin ? "Login" : "Register"}
            </button>
          </form>

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
