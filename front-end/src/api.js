import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000", // FastAPI URL
});

export const registerRetailer = (data) => API.post("/register/retailer", data);
export const loginRetailer = (data) => API.post("/login/retailer", data);
