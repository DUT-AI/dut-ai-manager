import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  LoginRequest,
  TokenResponse,
  RegisterRequest,
  ChangePasswordRequest,
  ZaloLoginUrlResponse,
  ZaloBindRequest,
  ZaloPhoneLoginRequest,
} from '@/types/auth.types';
import type { UserResponse } from '@/types/user.types';

export const authService = {
  login: async (data: LoginRequest): Promise<ApiResponse<TokenResponse>> => {
    const response = await axiosInstance.post<ApiResponse<TokenResponse>>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<ApiResponse<UserResponse>> => {
    const response = await axiosInstance.post<ApiResponse<UserResponse>>('/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.post<ApiResponse<null>>('/auth/logout');
    return response.data;
  },

  getMe: async (): Promise<ApiResponse<UserResponse>> => {
    const response = await axiosInstance.get<ApiResponse<UserResponse>>('/auth/me');
    return response.data;
  },

  changePassword: async (data: ChangePasswordRequest): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.post<ApiResponse<null>>('/auth/change-password', data);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<ApiResponse<TokenResponse>> => {
    const response = await axiosInstance.post<ApiResponse<TokenResponse>>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getZaloLoginUrl: async (): Promise<ApiResponse<ZaloLoginUrlResponse>> => {
    const response = await axiosInstance.get<ApiResponse<ZaloLoginUrlResponse>>('/zalo/login-url');
    return response.data;
  },

  bindZalo: async (data: ZaloBindRequest): Promise<ApiResponse<Record<string, unknown>>> => {
    const response = await axiosInstance.post<ApiResponse<Record<string, unknown>>>('/zalo/bind', data);
    return response.data;
  },

  loginWithZaloPhone: async (data: ZaloPhoneLoginRequest): Promise<ApiResponse<TokenResponse>> => {
    const response = await axiosInstance.post<ApiResponse<TokenResponse>>('/auth/zalo-phone-login', data);
    return response.data;
  },
};
