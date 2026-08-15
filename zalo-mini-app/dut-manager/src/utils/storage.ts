const STORAGE_KEYS = {
  ACCESS_TOKEN: 'dut_access_token',
  REFRESH_TOKEN: 'dut_refresh_token',
  USER_DATA: 'dut_user_data',
  SAVED_CREDENTIALS: 'dut_saved_credentials',
} as const;

export interface SavedCredentials {
  email?: string;
  password?: string;
  rememberMe?: boolean;
}

/**
 * An toàn đọc dữ liệu đồng bộ từ Storage.
 */
export const getItem = (key: string): string | null => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(key);
    }
  } catch (error) {
    console.warn(`[Storage] Failed to get item for key: ${key}`, error);
  }
  return null;
};

/**
 * An toàn lưu dữ liệu vào Storage.
 */
export const setItem = (key: string, value: string): void => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(key, value);
    }
  } catch (error) {
    console.warn(`[Storage] Failed to set item for key: ${key}`, error);
  }
};

/**
 * An toàn xóa dữ liệu trong Storage.
 */
export const removeItem = (key: string): void => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.removeItem(key);
    }
  } catch (error) {
    console.warn(`[Storage] Failed to remove item for key: ${key}`, error);
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

export const getSavedCredentials = (): SavedCredentials | null => {
  const data = getItem(STORAGE_KEYS.SAVED_CREDENTIALS);
  if (!data) return null;
  try {
    return JSON.parse(data) as SavedCredentials;
  } catch {
    return null;
  }
};

export const setSavedCredentials = (credentials: SavedCredentials | null): void => {
  if (credentials) {
    setItem(STORAGE_KEYS.SAVED_CREDENTIALS, JSON.stringify(credentials));
  } else {
    removeItem(STORAGE_KEYS.SAVED_CREDENTIALS);
  }
};

export const clearAllAuthData = (): void => {
  clearTokens();
  removeItem(STORAGE_KEYS.USER_DATA);
};
