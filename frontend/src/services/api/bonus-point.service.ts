import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { 
  BonusPointCreate,
  BonusPointUpdate,
  BonusPointResponse,
} from '@/types/activity.types';

export const bonusPointService = {
  subPath: 'bonus-points',

  async getBonusPoints(userId?: number, month?: number, year?: number) {
    const response = await axiosInstance.get<ApiResponse<BonusPointResponse[]>>(`/${this.subPath}`, {
        params: { user_id: userId, month, year }
    });
    return response.data;
  },

  async createBonusPoint(data: BonusPointCreate) {
    const response = await axiosInstance.post<ApiResponse<BonusPointResponse>>(`/${this.subPath}`, data);
    return response.data;
  },

  async updateBonusPoint(id: number, data: BonusPointUpdate) {
    const response = await axiosInstance.put<ApiResponse<BonusPointResponse>>(`/${this.subPath}/${id}`, data);
    return response.data;
  },

  async deleteBonusPoint(id: number) {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  },
};
