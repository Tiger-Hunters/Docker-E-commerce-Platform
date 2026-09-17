import axios from 'axios';

// The NGINX API Gateway Base URL
const API = axios.create({
  baseURL: 'http://localhost/api', 
});

// Intercept requests to add the JWT token if available
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- USER SERVICE ---
export const registerUser = (userData) => API.post('/users', userData);
export const loginUser = (credentials) => API.post('/users/login', credentials);
export const getUser = (id) => API.get(`/users/${id}`);

// --- PRODUCT SERVICE ---
export const getProducts = () => API.get('/products');
export const getProductById = (id) => API.get(`/products/${id}`);
export const createProduct = (productData) => API.post('/products', productData);
export const updateProduct = (id, productData) => API.put(`/products/${id}`, productData);
export const deleteProduct = (id) => API.delete(`/products/${id}`);

// --- ORDER SERVICE ---
export const createOrder = (orderData) => API.post('/orders', orderData);
export const getOrder = (id) => API.get(`/orders/${id}`);
export const getUserOrders = (userId) => API.get(`/users/${userId}/orders`);
export const updateOrderStatus = (id, status) => API.put(`/orders/${id}/status`, { status });
export const cancelOrder = (id) => API.delete(`/orders/${id}`);

export default API;