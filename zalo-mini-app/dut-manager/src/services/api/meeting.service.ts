import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  MeetingResponse,
  MeetingCreate,
  MeetingUpdate,
  ParticipantResponse,
} from '@/types/meeting.types';

export type MeetingItem = MeetingResponse;

export const meetingService = {
  subPath: 'meetings',

  async getMeetings(skip: number = 0, limit: number = 100): Promise<MeetingResponse[]> {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { skip, limit },
    });
    return response.data.data || [];
  },

  async getMeetingsByDateRange(startDate: string, endDate: string): Promise<MeetingResponse[]> {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { start_date: startDate, end_date: endDate, limit: 200 },
    });
    return response.data.data || [];
  },

  async getMeetingById(id: number): Promise<MeetingResponse | null> {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse>>(`/${this.subPath}/${id}`);
    return response.data.data || null;
  },

  async createMeeting(data: MeetingCreate): Promise<ApiResponse<MeetingResponse>> {
    const response = await axiosInstance.post<ApiResponse<MeetingResponse>>(`/${this.subPath}`, data);
    return response.data;
  },

  async updateMeeting(id: number, data: MeetingUpdate): Promise<ApiResponse<MeetingResponse>> {
    const response = await axiosInstance.put<ApiResponse<MeetingResponse>>(`/${this.subPath}/${id}`, data);
    return response.data;
  },

  async deleteMeeting(id: number): Promise<ApiResponse<boolean>> {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  },

  async checkIn(meetingId: number, userId: number, image: File): Promise<ApiResponse<ParticipantResponse>> {
    const formData = new FormData();
    formData.append('image', image);

    const response = await axiosInstance.post<ApiResponse<ParticipantResponse>>(
      `/${this.subPath}/check-in`,
      formData,
      {
        params: { meeting_id: meetingId, user_id: userId },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
