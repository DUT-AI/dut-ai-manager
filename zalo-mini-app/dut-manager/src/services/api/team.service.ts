import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface TeamSummary {
  id: number;
  name: string;
  description?: string | null;
}

export const teamService = {
  subPath: 'teams',

  async getTeams(skip = 0, limit = 100): Promise<TeamSummary[]> {
    const response = await axiosInstance.get<ApiResponse<TeamSummary[]>>(`/${this.subPath}`, {
      params: { skip, limit },
    });
    return response.data.data || [];
  },
};
