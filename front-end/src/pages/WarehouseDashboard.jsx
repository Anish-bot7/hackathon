import React, { useState, useEffect } from 'react';
import { useAuth } from '../Authcontext';
import { 
  getWarehouseStock, 
  addWarehouseStock, 
  getWarehouseOrders, 
  approveOrder, 
  rejectOrder,
  trainModels,
  getRestockPredictions,
  getAnalyticsDashboard
} from '../api';
import "../pages/dashboard.css"


const WarehouseDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stock, setStock] = useState([]);
  const [orders, setOrders] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [newStockItems, setNewStockItems] = useState([
    { product_id: '', product_name: '', quantity: '', price: '' }
  ]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.warehouse_id) {
      loadStock();
      loadOrders();
      loadAnalytics();
    }
  }, [user]);

  const loadStock = async () => {
    try {
      const response = await getWarehouseStock(user.warehouse_id);
      setStock(response.data.stock || []);
    } catch (error) {
      console.error('Error loading stock:', error);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await getWarehouseOrders(user.warehouse_id);
      setOrders(response.data.orders || []);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  const loadPredictions = async () => {
    try {
      const response = await getRestockPredictions(user.warehouse_id);
      setPredictions(response.data.predictions || []);
    } catch (error) {
      console.error('Error loading predictions:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await getAnalyticsDashboard(user.warehouse_id);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const handleStockSubmit = async (e) => {
    e.preventDefault();
    const validItems = newStockItems.filter(item => 
      item.product_id && item.product_name && item.quantity && item.price
    );

    if (validItems.length === 0) {
      alert('Please fill in all fields for at least one item');
      return;
    }

    try {
      await addWarehouseStock(user.warehouse_id, validItems.map(item => ({
        ...item,
        quantity: parseInt(item.quantity),
        price: parseFloat(item.price)
      })));
      alert('Stock updated successfully!');
      setNewStockItems([{ product_id: '', product_name: '', quantity: '', price: '' }]);
      loadStock();
    } catch (error) {
      alert('Error updating stock: ' + (error.response?.data?.detail || error.message));
    }
  };

  const addStockRow = () => {
    setNewStockItems([...newStockItems, { product_id: '', product_name: '', quantity: '', price: '' }]);
  };

  const updateStockItem = (index, field, value) => {
    const updated = [...newStockItems];
    updated[index][field] = value;
    setNewStockItems(updated);
  };

  const handleOrderAction = async (orderId, action) => {
    try {
      if (action === 'approve') {
        await approveOrder(orderId);
      } else {
        await rejectOrder(orderId);
      }
      loadOrders();
      loadStock(); // Refresh stock after approval
    } catch (error) {
      alert(`Error ${action}ing order: ` + (error.response?.data?.detail || error.message));
    }
  };

  const handleTrainModels = async () => {
    setLoading(true);
    try {
      await trainModels(user.warehouse_id);
      alert('Models trained successfully!');
      loadPredictions();
    } catch (error) {
      alert('Error training models: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const TabButton = ({ tabId, label, icon }) => (
    <button
      onClick={() => setActiveTab(tabId)}
      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
        activeTab === tabId 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
      }`}
    >
      {icon} {label}
    </button>
  );

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🏭 Warehouse Dashboard</h1>
      <p className="text-gray-600 mb-8">Welcome, {user?.name}!</p>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 mb-6">
        <TabButton tabId="overview" label="Overview" icon="📊" />
        <TabButton tabId="stock" label="Manage Stock" icon="📦" />
        <TabButton tabId="orders" label="Orders" icon="📋" />
        <TabButton tabId="predictions" label="AI Predictions" icon="🤖" />
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {analytics && (
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-2xl font-bold text-blue-600">{analytics.summary.total_products}</h3>
                <p className="text-gray-600">Total Products</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-2xl font-bold text-green-600">{analytics.summary.total_orders}</h3>
                <p className="text-gray-600">Total Orders</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-2xl font-bold text-yellow-600">{analytics.summary.pending_orders}</h3>
                <p className="text-gray-600">Pending Orders</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <h3 className="text-2xl font-bold text-red-600">{analytics.summary.low_stock_items}</h3>
                <p className="text-gray-600">Low Stock Items</p>
              </div>
            </div>
          )}

          {analytics?.low_stock_alerts?.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-red-600">⚠️ Low Stock Alerts</h2>
              <div className="space-y-2">
                {analytics.low_stock_alerts.map((item, idx) => (
                  <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded">
                    <span className="font-medium">{item.product_name}</span>
                    <span className="text-red-600 ml-2">Only {item.quantity} left!</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stock Management Tab */}
      {activeTab === 'stock' && (
        <div className="space-y-6">
          {/* Add New Stock */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">➕ Add/Update Stock</h2>
            <form onSubmit={handleStockSubmit}>
              {newStockItems.map((item, index) => (
                <div key={index} className="grid md:grid-cols-5 gap-4 mb-4">
                  <input
                    type="text"
                    placeholder="Product ID"
                    value={item.product_id}
                    onChange={(e) => updateStockItem(index, 'product_id', e.target.value)}
                    className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Product Name"
                    value={item.product_name}
                    onChange={(e) => updateStockItem(index, 'product_name', e.target.value)}
                    className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="number"
                    placeholder="Quantity"
                    value={item.quantity}
                    onChange={(e) => updateStockItem(index, 'quantity', e.target.value)}
                    className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Price"
                    value={item.price}
                    onChange={(e) => updateStockItem(index, 'price', e.target.value)}
                    className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={addStockRow}
                    className="bg-gray-600 text-white px-3 py-2 rounded hover:bg-gray-700"
                  >
                    + Row
                  </button>
                </div>
              ))}
              <button
                type="submit"
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Update Stock
              </button>
            </form>
          </div>

          {/* Current Stock */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">📦 Current Stock</h2>
            {stock.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="pb-2">Product ID</th>
                      <th className="pb-2">Product Name</th>
                      <th className="pb-2">Quantity</th>
                      <th className="pb-2">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stock.map((item, idx) => (
                      <tr key={idx} className="border-b">
                        <td className="py-2">{item.product_id}</td>
                        <td className="py-2">{item.product_name}</td>
                        <td className={`py-2 ${item.quantity < 10 ? 'text-red-600 font-bold' : ''}`}>
                          {item.quantity}
                        </td>
                        <td className="py-2">₹{item.price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No stock items found</p>
            )}
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">📋 Incoming Orders</h2>
          {orders.length > 0 ? (
            <div className="space-y-4">
              {orders.map(order => (
                <div key={order._id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium">Order #{order._id.slice(-6)}</h3>
                      <p className="text-sm text-gray-600">
                        {new Date(order.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded text-sm ${
                      order.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                      order.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>

                  <div className="mb-3">
                    <h4 className="font-medium text-sm mb-2">Items:</h4>
                    <div className="space-y-1">
                      {order.items?.map((item, idx) => (
                        <div key={idx} className="text-sm bg-gray-50 p-2 rounded">
                          {item.product_name} × {item.quantity}
                        </div>
                      ))}
                    </div>
                  </div>

                  {order.status === 'PENDING' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOrderAction(order._id, 'approve')}
                        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => handleOrderAction(order._id, 'reject')}
                        className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                      >
                        ✗ Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No orders found</p>
          )}
        </div>
      )}

      {/* AI Predictions Tab */}
      {activeTab === 'predictions' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">AI-Powered Restock Predictions</h2>
            <div className="mb-4">
              <button
                onClick={handleTrainModels}
                disabled={loading}
                className="bg-purple-600 text-white px-6 py-2 rounded mr-4 hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Training...' : 'Train AI Models'}
              </button>
              <button
                onClick={loadPredictions}
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                🔄 Refresh Predictions
              </button>
            </div>

            {predictions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="pb-2">Product</th>
                      <th className="pb-2">Current Stock</th>
                      <th className="pb-2">Daily Demand</th>
                      <th className="pb-2">Days to Reorder</th>
                      <th className="pb-2">Suggested Order</th>
                      <th className="pb-2">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((pred, idx) => (
                      <tr key={idx} className="border-b">
                        <td className="py-2">{pred.product_name}</td>
                        <td className="py-2">{pred.current_stock}</td>
                        <td className="py-2">{pred.avg_daily_demand}</td>
                        <td className={`py-2 ${pred.days_to_reorder < 3 ? 'text-red-600 font-bold' : ''}`}>
                          {pred.days_to_reorder}
                        </td>
                        <td className="py-2">{pred.suggested_order_qty}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            pred.confidence_level === 'HIGH' ? 'bg-green-100 text-green-800' :
                            pred.confidence_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {pred.confidence_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No predictions available. Train models first with order history.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WarehouseDashboard;