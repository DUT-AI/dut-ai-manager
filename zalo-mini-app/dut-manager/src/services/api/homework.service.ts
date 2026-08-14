import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface HomeworkItem {
  id: number;
  title: string;
  description?: string;
  deadline: string;
  status?: string;
}

export const homeworkService = {
  baseUrl: 'homeworks',

  async getAll(skip = 0, limit = 100): Promise<HomeworkItem[]> {
    const response = await axiosInstance.get<ApiResponse<HomeworkItem[]>>(`/${this.baseUrl}`, {
      params: { skip, limit, deleted: false },
    });
    return response.data.data || [];
  },
};
