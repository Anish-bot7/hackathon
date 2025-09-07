import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============== AUTH API ==============
export const registerRetailer = (data) => api.post('/auth/retailer/register', data);
export const loginRetailer = (data) => api.post('/auth/retailer/login', data);
export const registerWarehouse = (data) => api.post('/auth/warehouse/register', data);
export const loginWarehouse = (data) => api.post('/auth/warehouse/login', data);

// ============== RETAILER API ==============
export const getNearbyWarehouses = (retailerId) => api.get(`/retailers/${retailerId}/nearby-warehouses`);
export const getWarehouseProducts = (warehouseId) => api.get(`/warehouses/${warehouseId}/products`);
export const placeOrder = (orderData) => api.post('/orders', orderData);
export const getRetailerOrders = (retailerId) => api.get(`/retailers/${retailerId}/orders`);

// ============== WAREHOUSE API ==============
export const getWarehouseStock = (warehouseId) => api.get(`/warehouses/${warehouseId}/stock`);
export const addWarehouseStock = (warehouseId, stockItems) => api.post(`/warehouses/${warehouseId}/stock`, stockItems);
export const getWarehouseOrders = (warehouseId, status) => api.get(`/warehouses/${warehouseId}/orders${status ? `?status=${status}` : ''}`);
export const approveOrder = (orderId) => api.post(`/orders/${orderId}/approve`);
export const rejectOrder = (orderId) => api.post(`/orders/${orderId}/reject`);

// ============== ML/AI API ==============
export const trainModels = (warehouseId) => api.post(`/warehouses/${warehouseId}/train-models`);
export const getRestockPredictions = (warehouseId) => api.get(`/warehouses/${warehouseId}/restock-predictions`);
export const getDemandForecast = (productId, days = 7) => api.get(`/products/${productId}/demand-forecast?days=${days}`);
export const getAnalyticsDashboard = (warehouseId) => api.get(`/analytics/dashboard/${warehouseId}`);

// ============== PREDICTION API ==============
export const predictStockout = async (retailerId, currentStock) => {
  try {
    // This would typically be a separate endpoint, but we'll simulate it
    const predictions = {};
    for (const [productId, stock] of Object.entries(currentStock)) {
      const avgDemand = Math.random() * 3 + 1; // Simulated
      const daysLeft = stock / avgDemand;
      predictions[productId] = {
        daily_usage: avgDemand.toFixed(2),
        days_to_stockout: daysLeft.toFixed(1)
      };
    }
    
    const notifications = [];
    Object.entries(predictions).forEach(([pid, pred]) => {
      const days = parseFloat(pred.days_to_stockout);
      if (days < 3) {
        notifications.push({
          product_id: pid,
          message: `URGENT: Stock will finish in ${days.toFixed(1)} days`,
          priority: "HIGH"
        });
      } else if (days < 7) {
        notifications.push({
          product_id: pid,
          message: `WARNING: Stock will finish in ${days.toFixed(1)} days`,
          priority: "MEDIUM"
        });
      }
    });
    
    return {
      data: {
        daily_usage: Object.fromEntries(Object.entries(predictions).map(([k,v]) => [k, v.daily_usage])),
        days_to_stockout: Object.fromEntries(Object.entries(predictions).map(([k,v]) => [k, v.days_to_stockout])),
        notifications
      }
    };
  } catch (error) {
    throw error;
  }
};

export default api;