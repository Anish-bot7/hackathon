import React, { useState, useEffect } from 'react';
import { useAuth } from '../Authcontext';
import { getNearbyWarehouses, getWarehouseProducts, placeOrder, getRetailerOrders, predictStockout } from '../api';

const RetailerDashboard = () => {
  const { user } = useAuth();
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [currentStock, setCurrentStock] = useState({});
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.retailer_id) {
      loadWarehouses();
      loadOrders();
    }
  }, [user]);

  const loadWarehouses = async () => {
    try {
      const response = await getNearbyWarehouses(user.retailer_id);
      setWarehouses(response.data.warehouses || []);
    } catch (error) {
      console.error('Error loading warehouses:', error);
    }
  };

  const loadProducts = async (warehouseId) => {
    try {
      const response = await getWarehouseProducts(warehouseId);
      setProducts(response.data.products || []);
    } catch (error) {
      console.error('Error loading products:', error);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await getRetailerOrders(user.retailer_id);
      setOrders(response.data.orders || []);
    } catch (error) {
      console.error('Error loading orders:', error);
    }
  };

  const selectWarehouse = (warehouse) => {
    setSelectedWarehouse(warehouse);
    loadProducts(warehouse.warehouse_id);
  };

  const addToCart = (product) => {
    const quantity = parseInt(prompt(`Enter quantity for ${product.product_name}:`, '1'));
    if (quantity && quantity > 0) {
      const existingItem = cart.find(item => item.product_id === product.product_id);
      if (existingItem) {
        setCart(cart.map(item => 
          item.product_id === product.product_id 
            ? { ...item, quantity: item.quantity + quantity }
            : item
        ));
      } else {
        setCart([...cart, { ...product, quantity }]);
      }
    }
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const submitOrder = async () => {
    if (!selectedWarehouse || cart.length === 0) {
      alert('Please select a warehouse and add items to cart');
      return;
    }

    try {
      const orderData = {
        retailer_id: user.retailer_id,
        warehouse_id: selectedWarehouse.warehouse_id,
        items: cart.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: item.quantity
        }))
      };

      await placeOrder(orderData);
      alert('Order placed successfully!');
      setCart([]);
      loadOrders();
    } catch (error) {
      alert('Error placing order: ' + (error.response?.data?.detail || error.message));
    }
  };

  const runPrediction = async () => {
    if (Object.keys(currentStock).length === 0) {
      alert('Please enter current stock levels');
      return;
    }

    setLoading(true);
    try {
      const response = await predictStockout(user.retailer_id, currentStock);
      setPrediction(response.data);
    } catch (error) {
      alert('Error running prediction');
    } finally {
      setLoading(false);
    }
  };

  const addStockItem = () => {
    const productId = prompt('Enter Product ID:');
    const quantity = parseInt(prompt('Enter Current Stock:'));
    if (productId && quantity) {
      setCurrentStock({...currentStock, [productId]: quantity});
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">📦 Retailer Dashboard</h1>
      <p className="text-gray-600 mb-8">Welcome, {user?.name}!</p>
      {/* Nearby Warehouses */}
<h2 className="section-title">🏭 Nearby Warehouses</h2>
{warehouses.length > 0 ? (
  <div className="warehouses-grid">
    {warehouses.map(warehouse => (
      <div 
        key={warehouse.warehouse_id}
        className={`glass-box ${selectedWarehouse?.warehouse_id === warehouse.warehouse_id ? 'selected' : ''}`}
        onClick={() => selectWarehouse(warehouse)}
      >
        <h3 className="warehouse-name">{warehouse.name}</h3>
        <p className="warehouse-address">{warehouse.address}</p>
        <p className="warehouse-location">{warehouse.city}, {warehouse.region}</p>
      </div>
    ))}
  </div>
) : (
  <p className="text-gray-500">No warehouses found in your area</p>
)}


      {/* Products */}
      {selectedWarehouse && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📋 Products at {selectedWarehouse.name}</h2>
          {products.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b">
                    <th className="pb-2">Product</th>
                    <th className="pb-2">Available</th>
                    <th className="pb-2">Price</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(product => (
                    <tr key={product.product_id} className="border-b">
                      <td className="py-2">{product.product_name}</td>
                      <td className="py-2">{product.quantity}</td>
                      <td className="py-2">₹{product.price}</td>
                      <td className="py-2">
                        <button 
                          onClick={() => addToCart(product)}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Add to Cart
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">No products available</p>
          )}
        </div>
      )}

      {/* Cart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">🛒 Shopping Cart</h2>
        {cart.length > 0 ? (
          <>
            <div className="space-y-2 mb-4">
              {cart.map(item => (
                <div key={item.product_id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>{item.product_name} × {item.quantity}</span>
                  <button 
                    onClick={() => removeFromCart(item.product_id)}
                    className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <button 
              onClick={submitOrder}
              className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
            >
              Place Order
            </button>
          </>
        ) : (
          <p className="text-gray-500">Cart is empty</p>
        )}
      </div>

      {/* Stock Prediction */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">🔮 Stock Prediction (AI)</h2>
        <div className="mb-4">
          <h3 className="font-medium mb-2">Current Stock Levels:</h3>
          <div className="space-y-2 mb-3">
            {Object.entries(currentStock).map(([productId, quantity]) => (
              <div key={productId} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>Product {productId}: {quantity} units</span>
                <button 
                  onClick={() => {
                    const newStock = {...currentStock};
                    delete newStock[productId];
                    setCurrentStock(newStock);
                  }}
                  className="text-red-600 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button 
            onClick={addStockItem}
            className="bg-gray-600 text-white px-4 py-2 rounded mr-2 hover:bg-gray-700"
          >
            Add Stock Item
          </button>
          <button 
            onClick={runPrediction}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? 'Predicting...' : 'Run Prediction'}
          </button>
        </div>

        {prediction && (
          <div className="border-t pt-4">
            <h3 className="font-medium mb-3">Prediction Results:</h3>
            
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="font-medium text-sm mb-2">Daily Usage:</h4>
                <div className="space-y-1">
                  {Object.entries(prediction.daily_usage).map(([pid, usage]) => (
                    <div key={pid} className="text-sm">Product {pid}: {usage} units/day</div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-2">Days to Stockout:</h4>
                <div className="space-y-1">
                  {Object.entries(prediction.days_to_stockout).map(([pid, days]) => (
                    <div key={pid} className="text-sm">Product {pid}: {days} days</div>
                  ))}
                </div>
              </div>
            </div>

            {prediction.notifications?.length > 0 && (
              <div>
                <h4 className="font-medium text-sm mb-2">⚠️ Alerts:</h4>
                <div className="space-y-2">
                  {prediction.notifications.map((notification, idx) => (
                    <div 
                      key={idx} 
                      className={`p-2 rounded text-sm ${
                        notification.priority === 'HIGH' 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      Product {notification.product_id}: {notification.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Order History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">📋 Order History</h2>
        {orders.length > 0 ? (
          <div className="space-y-3">
            {orders.map(order => (
              <div key={order._id} className="p-4 border rounded">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium">Order #{order._id.slice(-6)}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    order.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                    order.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {order.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  {new Date(order.created_at).toLocaleDateString()}
                </p>
                <div className="text-sm">
                  Items: {order.items?.map(item => `${item.product_name} (${item.quantity})`).join(', ')}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No orders yet</p>
        )}
      </div>
    </div>
  );
};

export default RetailerDashboard;