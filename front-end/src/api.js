import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

// ---- AUTH ----
export const registerRetailer = (payload) => API.post("/auth/retailer/register", payload);
export const loginRetailer = (payload) => API.post("/auth/retailer/login", payload);
export const registerWarehouse = (payload) => API.post("/auth/warehouse/register", payload);
export const loginWarehouse = (payload) => API.post("/auth/warehouse/login", payload);

// ---- DASHBOARDS ----
export const getNearbyWarehouses = (retailerId, radiusKm = 10) =>
  API.get(`/retailers/${retailerId}/nearby-warehouses?radius_km=${radiusKm}`);

export const getWarehouseStock = (warehouseId) =>
  API.get(`/warehouses/${warehouseId}/stock`);

export const upsertWarehouseStock = (warehouseId, items) =>
  API.post(`/warehouses/${warehouseId}/stock`, items);

export const placeOrder = (order) => API.post("/orders", order);

export const getDefaultOrder = (retailerId) =>
  API.get(`/retailers/${retailerId}/default-order`);

export const getWarehouseOrders = (warehouseId) =>
  API.get(`/warehouses/${warehouseId}/orders`);

export const predictStockout = (retailerId, currentOnHand) =>
  API.post(`/retailers/${retailerId}/predict-stockout`, { current_on_hand: currentOnHand || {} });
