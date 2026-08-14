import { nativeStorage } from 'zmp-sdk';

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'dut_access_token',
  REFRESH_TOKEN: 'dut_refresh_token',
  USER_DATA: 'dut_user_data',
} as const;

/**
 * An toàn đọc dữ liệu từ nativeStorage của ZMP SDK với fallback.
 */
export const getItem = (key: string): string | null => {
  try {
    if (typeof nativeStorage !== 'undefined' && typeof nativeStorage.getItem === 'function') {
      const value = nativeStorage.getItem(key);
      if (value !== undefined && value !== null) {
        return typeof value === 'string' ? value : JSON.stringify(value);
      }
    }
  } catch (error) {
    console.warn(`[ZMP Storage] Failed to get item for key: ${key}`, error);
  }

  // Fallback to localStorage if in browser environment
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return localStorage.getItem(key);
    }
  } catch {
    // Ignore fallback errors
  }

  return null;
};

/**
 * An toàn lưu dữ liệu vào nativeStorage của ZMP SDK.
 */
export const setItem = (key: string, value: string): void => {
  try {
    if (typeof nativeStorage !== 'undefined' && typeof nativeStorage.setItem === 'function') {
      nativeStorage.setItem(key, value);
    }
  } catch (error) {
    console.warn(`[ZMP Storage] Failed to set item for key: ${key}`, error);
  }

  // Fallback to localStorage
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(key, value);
    }
  } catch {
    // Ignore fallback errors
  }
};

/**
 * An toàn xóa dữ liệu trong nativeStorage của ZMP SDK.
 */
export const removeItem = (key: string): void => {
  try {
    if (typeof nativeStorage !== 'undefined' && typeof nativeStorage.removeItem === 'function') {
      nativeStorage.removeItem(key);
    }
  } catch (error) {
    console.warn(`[ZMP Storage] Failed to remove item for key: ${key}`, error);
  }

  // Fallback to localStorage
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.removeItem(key);
    }
  } catch {
    // Ignore fallback errors
  }
};

/**
 * Helpers quản lý Tokens và Session người dùng
 */
export const getAccessToken = (): string | null => {
  return getItem(STORAGE_KEYS.ACCESS_TOKEN);
};

export const setAccessToken = (token: string): void => {
  setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
};

export const getRefreshToken = (): string | null => {
  return getItem(STORAGE_KEYS.REFRESH_TOKEN);
};

export const setRefreshToken = (token: string): void => {
  setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  setAccessToken(accessToken);
  setRefreshToken(refreshToken);
};

export const clearTokens = (): void => {
  removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  removeItem(STORAGE_KEYS.REFRESH_TOKEN);
};

export const getUserData = <T = unknown>(): T | null => {
  const data = getItem(STORAGE_KEYS.USER_DATA);
  if (!data) return null;
  try {
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
};

export const setUserData = (user: unknown): void => {
  if (user) {
    setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
  } else {
    removeItem(STORAGE_KEYS.USER_DATA);
  }
};

export const clearAllAuthData = (): void => {
  clearTokens();
  removeItem(STORAGE_KEYS.USER_DATA);
};
