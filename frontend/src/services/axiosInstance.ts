import axios from 'axios';
import { message } from 'antd';

const API_BASE_URL = import.meta.env.VITE_API_URL;

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear session information
      // Session is effectively cleared by the cookie being invalid or expiried

      
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
        message.error('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.');
        // Use setTimeout to allow the message to be seen briefly/process before redirect
        // although window.location will reload the page immediately usually.
        // For a smoother experience in a real app we might use react-router's navigate,
        // but axiosInstance is outside React context.
        window.location.href = '/login';
      }
    }

    // Extract error message from API response if available
    if (error.response?.data?.message) {
      error.message = error.response.data.message;
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
