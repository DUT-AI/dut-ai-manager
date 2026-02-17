import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { MeetingCreate, MeetingUpdate, MeetingResponse, ParticipantResponse } from '@/types/meeting.types';

export const meetingService = {
  subPath: 'meetings',

  async getMeetings(skip: number = 0, limit: number = 100) {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { skip, limit }
    });
    return response.data;
  },

  async getMeetingsByDateRange(startDate: string, endDate: string) {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { start_date: startDate, end_date: endDate, limit: 200 }
    });
    return response.data;
  },

  async getMeetingById(id: number) {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse>>(`/${this.subPath}/${id}`);
    return response.data;
  },

  async createMeeting(data: MeetingCreate) {
    const response = await axiosInstance.post<ApiResponse<MeetingResponse>>(`/${this.subPath}`, data);
    return response.data;
  },

  async checkIn(meetingId: number, userId: number, image: File) {
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

  async updateMeeting(id: number, data: MeetingUpdate) {
    const response = await axiosInstance.put<ApiResponse<MeetingResponse>>(`/${this.subPath}/${id}`, data);
    return response.data;
  },

  async deleteMeeting(id: number) {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  }
};
