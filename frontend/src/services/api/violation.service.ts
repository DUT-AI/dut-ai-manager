import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { ViolationResponse } from '@/types/activity.types';

export const violationService = {
  getViolations: async (skip = 0, limit = 100, userId?: number, month?: number, year?: number, deleted?: boolean) => {
    const response = await axiosInstance.get<ApiResponse<ViolationResponse[]>>('/violations', {
      params: { skip, limit, user_id: userId, month, year, deleted },
    });
    return response.data.data;
  },

  createViolation: async (data: any) => {
    const response = await axiosInstance.post<ApiResponse<ViolationResponse[]>>('/violations', data);
    return response.data;
  },

  updateViolation: async (id: number, data: any) => {
    const response = await axiosInstance.put<ApiResponse<ViolationResponse>>(`/violations/${id}`, data);
    return response.data;
  },

  deleteViolation: async (id: number) => {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/violations/${id}`);
    return response.data;
  },

  restoreViolation: async (id: number) => {
    const response = await axiosInstance.put<ApiResponse<ViolationResponse>>(`/violations/${id}/restore`);
    return response.data;
  }
};
