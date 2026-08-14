import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface UserSummary {
  id: number;
  name: string;
  email: string;
  avatar_url?: string | null;
  role_names?: string[];
}

export const userService = {
  getUsers: async (): Promise<UserSummary[]> => {
    const response = await axiosInstance.get<ApiResponse<UserSummary[]>>('/users');
    return response.data.data || [];
  },
};
