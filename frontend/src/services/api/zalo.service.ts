import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { UserResponse } from '@/types/user.types';

export const zaloService = {
  /**
   * Get Zalo Login URL for OAuth flow
   */
  getLoginUrl: async () => {
    const response = await axiosInstance.get<ApiResponse<{ login_url: string; code_verifier: string }>>('/zalo/login-url');
    return response.data;
  },

  /**
   * Generate new Bind Code for Zalo Bot Webhook
   */
  getBotBindCode: async () => {
    const response = await axiosInstance.get<ApiResponse<{ bind_code: string }>>('/zalo-bot/generate-bind-code');
    return response.data;
  },

  /**
   * Bind user's Zalo account using oauth code
   * @param oauth_code The code received from Zalo Login callback
   * @param code_verifier The PKCE verifier generated before
   */
  bindZaloAccount: async (oauth_code: string, code_verifier: string) => {
    const response = await axiosInstance.post<ApiResponse<UserResponse>>('/zalo/bind', {
      oauth_code,
      code_verifier
    });
    return response.data;
  },
};
