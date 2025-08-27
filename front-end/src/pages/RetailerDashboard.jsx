import React from "react";
import { useNavigate } from "react-router-dom";

function RetailerDashboard() {
  const navigate = useNavigate();

  // Sample data for nearby warehouses
  const warehouses = [
    { id: 1, name: "Warehouse A", distance: "2 km" },
    { id: 2, name: "Warehouse B", distance: "5 km" },
    { id: 3, name: "Warehouse C", distance: "8 km" },
  ];

  // Sample data for retailer orders
  const myOrders = [
    { id: 101, item: "Rice 50kg", status: "Delivered" },
    { id: 102, item: "Wheat 20kg", status: "In Transit" },
    { id: 103, item: "Sugar 10kg", status: "Pending" },
  ];

  const handleLogout = () => {
    // Clear session/local storage if needed
    localStorage.removeItem("token");
    navigate("/retailer");
  };

  return (
    <div className="p-6 min-h-screen bg-gray-100">
      {/* Top Navbar */}
      <div className="flex justify-between items-center bg-blue-600 text-white p-4 rounded-lg shadow-md">
        <h1 className="text-xl font-bold">Retailer Dashboard</h1>
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg"
        >
          Logout
        </button>
      </div>

      {/* Nearby Warehouses Section */}
      <div className="mt-6 bg-white shadow-md p-6 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Nearby Warehouses</h2>
        <ul className="space-y-2">
          {warehouses.map((w) => (
            <li
              key={w.id}
              className="flex justify-between p-3 border rounded-md bg-gray-50"
            >
              <span>{w.name}</span>
              <span className="text-sm text-gray-500">{w.distance}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* My Orders Section */}
      <div className="mt-6 bg-white shadow-md p-6 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">My Orders</h2>
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-200">
              <th className="p-2 border">Order ID</th>
              <th className="p-2 border">Item</th>
              <th className="p-2 border">Status</th>
            </tr>
          </thead>
          <tbody>
            {myOrders.map((o) => (
              <tr key={o.id} className="text-center">
                <td className="p-2 border">{o.id}</td>
                <td className="p-2 border">{o.item}</td>
                <td className="p-2 border">{o.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RetailerDashboard;
