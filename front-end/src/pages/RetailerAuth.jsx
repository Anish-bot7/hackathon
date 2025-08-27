import React, { useState } from "react";
import "./Login.css";
import { FaLock, FaMapMarkerAlt, FaStore } from "react-icons/fa";
import { registerRetailer, loginRetailer, loginWarehouse, registerWarehouse } from "../api";
import { useNavigate } from "react-router-dom";

export default function RetailerAuth() {
  const [isRetailer, setIsRetailer] = useState(true);
  const [isLogin, setIsLogin] = useState(true);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [locationName, setLocationName] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isRetailer) {
        if (isLogin) {
          const { data } = await loginRetailer({ email, password });
          localStorage.setItem("retailer", JSON.stringify(data));
          navigate("/retailer");
        } else {
          await registerRetailer({ name, email, password, location_name: locationName, lat: Number(lat), lng: Number(lng) });
          alert("Retailer registered. Now login.");
          setIsLogin(true);
        }
      } else {
        if (isLogin) {
          const { data } = await loginWarehouse({ email, password });
          localStorage.setItem("warehouse", JSON.stringify(data));
          navigate("/warehouse");
        } else {
          await registerWarehouse({ name, email, password, location_name: locationName, lat: Number(lat), lng: Number(lng) });
          alert("Warehouse registered. Now login.");
          setIsLogin(true);
        }
      }
    } catch (err) {
      alert(err?.response?.data?.detail || "Error");
    }
  };

  return (
    <div className="login-container">
      <nav className="login-navbar">
        <h1>Smart Supply Chain</h1>
      </nav>

      <main className="login-main">
        <div className="login-card">
          <h2>{isLogin ? "Login" : "Register"} as {isRetailer ? "Retailer" : "Warehouse"}</h2>
          <p>Switch Role:{" "}
            <button className="login-btn warehouse" onClick={() => setIsRetailer(v => !v)}>
              {isRetailer ? "Use Warehouse" : "Use Retailer"}
            </button>
          </p>

          <form onSubmit={handleSubmit} style={{display: "grid", gap: 12}}>
            {!isLogin && (
              <>
                <input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} required />
                <input placeholder="Location Name" value={locationName} onChange={e=>setLocationName(e.target.value)} required />
                <input placeholder="Latitude" value={lat} onChange={e=>setLat(e.target.value)} required />
                <input placeholder="Longitude" value={lng} onChange={e=>setLng(e.target.value)} required />
              </>
            )}
            <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required />
            <input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />

            <div style={{display:"flex", gap:10, justifyContent:"center"}}>
              <button className="login-btn retailer" type="submit">
                {isLogin ? "Login" : "Register"}
              </button>
              <button type="button" className="login-btn warehouse" onClick={() => setIsLogin(v=>!v)}>
                {isLogin ? "Create Account" : "Have Account?"}
              </button>
            </div>
          </form>
        </div>
      </main>

      <footer className="login-footer">
        <p>© Smart Supply Chain</p>
      </footer>
    </div>
  );
}
