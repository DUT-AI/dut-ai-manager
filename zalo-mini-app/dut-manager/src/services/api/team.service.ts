import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface TeamSummary {
  id: number;
  name: string;
  description?: string | null;
}

export const teamService = {
  subPath: 'teams',

  async getTeams(page = 1, pageSize = 20): Promise<TeamSummary[]> {
    const response = await axiosInstance.get<ApiResponse<TeamSummary[]>>(`/${this.subPath}`, {
      params: { page, page_size: pageSize },
    });
    return response.data.data || [];
  },
};
