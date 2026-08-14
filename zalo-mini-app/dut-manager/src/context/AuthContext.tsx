import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '@/services/api/auth.service';
import type { LoginRequest, TokenResponse } from '@/types/auth.types';
import type { UserResponse } from '@/types/user.types';
import type { ApiResponse } from '@/types/api.types';
import {
  getAccessToken,
  setTokens,
  getUserData,
  setUserData,
  clearAllAuthData,
} from '@/utils/storage';

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<ApiResponse<TokenResponse>>;
  loginWithZaloPhone: (phoneToken: string) => Promise<ApiResponse<TokenResponse>>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<UserResponse | null>;
  hasPermission: (permission: string) => boolean;
  isAdminOrLeader: () => boolean;
  isAdmin: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Khởi tạo từ cache ZMP Storage để giao diện hiển thị tức thì
  const [user, setUser] = useState<UserResponse | null>(() => getUserData<UserResponse>());
  const [loading, setLoading] = useState<boolean>(true);

  const fetchUser = useCallback(async (): Promise<UserResponse | null> => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setUserData(null);
      return null;
    }

    try {
      const response = await authService.getMe();
      if (response.is_success && response.data) {
        setUser(response.data);
        setUserData(response.data);
        return response.data;
      } else {
        setUser(null);
        clearAllAuthData();
        return null;
      }
    } catch (error) {
      console.warn('[AuthContext] Failed to fetch current user profile:', error);
      // Nếu có lỗi xác thực, dọn dẹp storage
      const cached = getUserData<UserResponse>();
      if (!cached) {
        setUser(null);
        clearAllAuthData();
      }
      return null;
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);
      await fetchUser();
      setLoading(false);
    };

    initAuth();
  }, [fetchUser]);

  const login = async (data: LoginRequest): Promise<ApiResponse<TokenResponse>> => {
    setLoading(true);
    try {
      const response = await authService.login(data);
      if (response.is_success && response.data) {
        const { access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);
        await fetchUser();
      }
      return response;
    } finally {
      setLoading(false);
    }
  };

  const loginWithZaloPhone = async (phoneToken: string): Promise<ApiResponse<TokenResponse>> => {
    setLoading(true);
    try {
      const response = await authService.loginWithZaloPhone({ phone_token: phoneToken });
      if (response.is_success && response.data) {
        const { access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);
        await fetchUser();
      }
      return response;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.warn('[AuthContext] Logout API error:', error);
    } finally {
      clearAllAuthData();
      setUser(null);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    const roles = user.role_names?.map((r) => r.toLowerCase()) || [];
    if (roles.includes('admin')) return true;
    return user.permission_names?.includes(permission) || false;
  };

  const isAdminOrLeader = (): boolean => {
    if (!user) return false;
    const roles = user.role_names?.map((r) => r.toLowerCase()) || [];
    return roles.includes('admin') || roles.includes('leader');
  };

  const isAdmin = (): boolean => {
    if (!user) return false;
    const roles = user.role_names?.map((r) => r.toLowerCase()) || [];
    return roles.includes('admin');
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user && !!getAccessToken(),
    login,
    loginWithZaloPhone,
    logout,
    refreshUser: fetchUser,
    hasPermission,
    isAdminOrLeader,
    isAdmin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
