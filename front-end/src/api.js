import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('userType');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  loginRetailer: (credentials) => api.post('/auth/retailer/login', credentials),
  loginWarehouse: (credentials) => api.post('/auth/warehouse/login', credentials),
  registerRetailer: (userData) => api.post('/auth/retailer/register', userData),
  registerWarehouse: (userData) => api.post('/auth/warehouse/register', userData),
};

export const retailerAPI = {
  getNearbyWarehouses: (retailerId) =>
    api.get(`/retailers/${retailerId}/nearby-warehouses`),
  getOrders: (retailerId, status) =>
    api.get(`/retailers/${retailerId}/orders${status ? `?status=${status}` : ''}`),
  placeOrder: (orderData) => api.post('/orders', orderData),
};

export const warehouseAPI = {
  getNearbyRetailers: (warehouseId) =>
    api.get(`/warehouses/${warehouseId}/nearby-retailers`),
  getStock: (warehouseId) =>
    api.get(`/warehouses/${warehouseId}/stock`),
  addStock: (warehouseId, stockItems) =>
    api.post(`/warehouses/${warehouseId}/stock`, stockItems),
  getOrders: (warehouseId, status) =>
    api.get(`/orders/warehouse/${warehouseId}${status ? `?status=${status}` : ''}`),
  approveOrder: (orderId) =>
    api.post(`/orders/${orderId}/approve`),
  rejectOrder: (orderId) =>
    api.post(`/orders/${orderId}/reject`),
  getProducts: (warehouseId) =>
    api.get(`/warehouses/${warehouseId}/products`),
  trainModels: (warehouseId) =>
    api.post(`/warehouses/${warehouseId}/train-models`),
  getRestockPredictions: (warehouseId) =>
    api.get(`/warehouses/${warehouseId}/restock-predictions`),
  getDemandForecast: (productId, days) =>
    api.get(`/products/${productId}/demand-forecast?days=${days || 14}`),
  getAnalytics: (warehouseId) =>
    api.get(`/analytics/dashboard/${warehouseId}`),
};
