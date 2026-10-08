import axiosInstance from '../../../services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  MeetingCreate,
  MeetingUpdate,
  MeetingResponse,
  MeetingDetailResponse,
  ParticipantResponse,
  UpdateParticipantStatusPayload,
  MeetingSeatAvailabilityDto,
} from '@/features/meeting/types/meeting.types';

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
    const response = await axiosInstance.get<ApiResponse<MeetingDetailResponse>>(`/${this.subPath}/${id}`);
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

  async updateParticipantStatus(meetingId: number, userId: number, payload: UpdateParticipantStatusPayload) {
    const response = await axiosInstance.put<ApiResponse<ParticipantResponse>>(
      `/${this.subPath}/${meetingId}/participants/${userId}/status`,
      payload
    );
    return response.data;
  },

  async deleteMeeting(id: number) {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  },

  async submitTrainerEvaluation(meetingId: number, payload: import('@/features/meeting/types/meeting.types').TrainerSubmitEvaluationPayload) {
    const response = await axiosInstance.post<ApiResponse<import('@/features/meeting/types/meeting.types').EvaluationResponse>>(
      `/${this.subPath}/${meetingId}/evaluations/trainer`,
      payload
    );
    return response.data;
  },

  async submitTraineeEvaluation(meetingId: number, payload: import('@/features/meeting/types/meeting.types').TraineeSubmitEvaluationPayload) {
    const response = await axiosInstance.post<ApiResponse<import('@/features/meeting/types/meeting.types').EvaluationResponse>>(
      `/${this.subPath}/${meetingId}/evaluations/trainee`,
      payload
    );
    return response.data;
  },

  async getMeetingEvaluationSummary(meetingId: number) {
    const response = await axiosInstance.get<ApiResponse<import('@/features/meeting/types/meeting.types').MeetingEvaluationSummary>>(
      `/${this.subPath}/${meetingId}/evaluations/summary`
    );
    return response.data;
  },

  async getMyEvaluationResult(meetingId: number) {
    const response = await axiosInstance.get<ApiResponse<import('@/features/meeting/types/meeting.types').EvaluationResponse | null>>(
      `/${this.subPath}/${meetingId}/evaluations/my-result`
    );
    return response.data;
  },

  async getAvailableSeats(fromDate?: string) {
    const response = await axiosInstance.get<ApiResponse<MeetingSeatAvailabilityDto[]>>(
      `/${this.subPath}/available-seats`,
      { params: fromDate ? { from_date: fromDate } : undefined }
    );
    return response.data;
  }
};

