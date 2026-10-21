import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface TeamMemberSummary {
  user_id: number;
  user_name: string;
  email: string;
  user_avatar_url?: string | null;
}

export interface TeamSummary {
  id: number;
  team_name: string;
  member_count?: number;
  members?: TeamMemberSummary[];
  description?: string | null;
}

export const teamService = {
  subPath: 'teams',

  async getTeams(page = 1, pageSize = 100): Promise<TeamSummary[]> {
    const response = await axiosInstance.get<ApiResponse<TeamSummary[]>>(`/${this.subPath}`, {
      params: { page, page_size: pageSize },
    });
    return response.data.data || [];
  },
};
