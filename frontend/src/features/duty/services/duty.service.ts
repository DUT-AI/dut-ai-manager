import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  DutyResponse,
  WeeklyDutyClassDto,
  ToggleDutyScheduleRequest,
  BatchCreateDutyRequest,
} from '../types/duty.types';

export const dutyService = {
  subPath: 'duties',

  async getWeeklySchedule(targetDate?: string) {
    const response = await axiosInstance.get<ApiResponse<WeeklyDutyClassDto[]>>(
      `/${this.subPath}/weekly`,
      { params: { target_date: targetDate } }
    );
    return response.data;
  },

  async getDuties(params?: {
    start_date?: string;
    end_date?: string;
    team_id?: number;
    status?: string;
    page?: number;
    page_size?: number;
  }) {
    const response = await axiosInstance.get<ApiResponse<DutyResponse[]>>(
      `/${this.subPath}`,
      { params }
    );
    return response.data;
  },

  async getDutyById(id: number) {
    const response = await axiosInstance.get<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${id}`
    );
    return response.data;
  },

  async toggleSchedule(data: ToggleDutyScheduleRequest) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse | null>>(
      `/${this.subPath}/toggle-schedule`,
      data
    );
    return response.data;
  },

  async batchCreateDuties(data: BatchCreateDutyRequest) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse[]>>(
      `/${this.subPath}/batch-schedule`,
      data
    );
    return response.data;
  },

  async submitEvidence(
    dutyId: number,
    formData: FormData
  ) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${dutyId}/submit`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async approveDuty(dutyId: number) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${dutyId}/approve`
    );
    return response.data;
  },

  async rejectDuty(dutyId: number, reason: string) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${dutyId}/reject`,
      { reason }
    );
    return response.data;
  },

  async updateDuty(dutyId: number, data: import('../types/duty.types').UpdateDutyRequest) {
    const response = await axiosInstance.put<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${dutyId}`,
      data
    );
    return response.data;
  },

  async deleteDuty(dutyId: number) {
    const response = await axiosInstance.delete<ApiResponse<null>>(
      `/${this.subPath}/${dutyId}`
    );
    return response.data;
  },

  async restoreDuty(dutyId: number) {
    const response = await axiosInstance.post<ApiResponse<DutyResponse>>(
      `/${this.subPath}/${dutyId}/restore`
    );
    return response.data;
  },
};
