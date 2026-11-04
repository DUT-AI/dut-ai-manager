import axios from 'axios';
import { message } from 'antd';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

interface QueueItem {
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];
let isRedirectingToLogin = false;

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export const resetSessionExpiredState = () => {
  isRedirectingToLogin = false;
};

const handleSessionExpired = (error: unknown) => {
  if (isRedirectingToLogin) {
    return;
  }

  // Bỏ qua nếu lỗi là do thiếu token (người dùng chưa từng đăng nhập / khách vãng lai)
  const isMissingToken =
    (error as any)?.response?.data?.message?.toLowerCase()?.includes('missing') ||
    (error as any)?.message?.toLowerCase()?.includes('missing');

  if (isMissingToken) {
    return;
  }

  isRedirectingToLogin = true;

  const currentPath = window.location.pathname;

  // Chỉ hiển thị thông báo và chuyển hướng nếu không phải đang ở trang đăng nhập hoặc callback
  if (currentPath !== '/login' && !currentPath.startsWith('/auth/zalo/callback')) {
    message.error('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.');
    setTimeout(() => {
      window.location.href = '/login';
      setTimeout(() => {
        isRedirectingToLogin = false;
      }, 1000);
    }, 1500);
  } else {
    isRedirectingToLogin = false;
  }
};

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Nếu không có response hoặc config, reject lỗi ngay
    if (!error.response || !originalRequest) {
      return Promise.reject(error);
    }

    const requestUrl = originalRequest.url || '';

    // Xử lý mã lỗi 401 Unauthorized
    if (error.response.status === 401) {
      // 1. Chống vòng lặp vô tận & bỏ qua các endpoint xác thực/đang ở trang login
      const isAuthEndpoint =
        requestUrl.includes('/auth/login') ||
        requestUrl.includes('/auth/refresh') ||
        requestUrl.includes('/auth/register');

      if (
        originalRequest._retry ||
        isAuthEndpoint ||
        window.location.pathname === '/login'
      ) {
        if (requestUrl.includes('/auth/refresh')) {
          handleSessionExpired(error);
        }
        return Promise.reject(error);
      }

      // 2. Nếu đang có một tiến trình refresh chạy dở, đưa request vào hàng đợi
      if (isRefreshing) {
        originalRequest._retry = true;
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      // 3. Khóa trạng thái refresh và bắt đầu gọi /auth/refresh
      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        if (refreshResponse.data?.is_success) {
          processQueue(null);
          return axiosInstance(originalRequest);
        } else {
          const refreshError = new Error(
            refreshResponse.data?.message || 'Refresh token failed'
          );
          processQueue(refreshError, null);
          handleSessionExpired(refreshError);
          return Promise.reject(refreshError);
        }
      } catch (refreshError: unknown) {
        processQueue(refreshError, null);
        handleSessionExpired(refreshError);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Trích xuất error message từ backend nếu có
    if (error.response?.data?.message) {
      error.message = error.response.data.message;
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
