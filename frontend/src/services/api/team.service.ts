import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { TeamResponse, TeamCreate, TeamUpdate } from '@/types/team.types';

export const teamService = {
  subPath: 'teams',

  async getTeams(skip = 0, limit = 100) {
    const response = await axiosInstance.get<ApiResponse<TeamResponse[]>>(`/${this.subPath}`, {
      params: { skip, limit }
    });
    return response.data;
  },

  async getTeam(id: number) {
    const response = await axiosInstance.get<ApiResponse<TeamResponse>>(`/${this.subPath}/${id}`);
    return response.data;
  },

  async createTeam(data: TeamCreate) {
    const response = await axiosInstance.post<ApiResponse<TeamResponse>>(`/${this.subPath}`, data);
    return response.data;
  },

  async updateTeam(id: number, data: TeamUpdate) {
    const response = await axiosInstance.put<ApiResponse<TeamResponse>>(`/${this.subPath}/${id}`, data);
    return response.data;
  },

  async deleteTeam(id: number) {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  }
};
