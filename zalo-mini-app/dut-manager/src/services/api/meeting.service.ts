import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  MeetingResponse,
  MeetingDetailResponse,
  MeetingCreate,
  MeetingUpdate,
  ParticipantResponse,
  UpdateParticipantStatusPayload,
  SubmitMeetingOverallEvaluationPayload,
  MeetingOverallEvaluationResponse,
  TrainerSubmitEvaluationPayload,
  TraineeSubmitEvaluationPayload,
  EvaluationResponse,
  MeetingEvaluationSummary,
  MeetingSeatAvailabilityDto,
} from '@/types/meeting.types';

export type MeetingItem = MeetingResponse;

export const meetingService = {
  subPath: 'meetings',

  async getMeetings(page: number = 1, pageSize: number = 20): Promise<MeetingResponse[]> {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { page, page_size: pageSize },
    });
    return response.data.data || [];
  },

  async getMeetingsByDateRange(startDate: string, endDate: string): Promise<MeetingResponse[]> {
    const response = await axiosInstance.get<ApiResponse<MeetingResponse[]>>(`/${this.subPath}`, {
      params: { start_date: startDate, end_date: endDate, limit: 200 },
    });
    return response.data.data || [];
  },

  async getMeetingById(id: number): Promise<MeetingDetailResponse | null> {
    const response = await axiosInstance.get<ApiResponse<MeetingDetailResponse>>(`/${this.subPath}/${id}`);
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

  async updateParticipantStatus(
    meetingId: number,
    userId: number,
    payload: UpdateParticipantStatusPayload
  ): Promise<ApiResponse<ParticipantResponse>> {
    const response = await axiosInstance.put<ApiResponse<ParticipantResponse>>(
      `/${this.subPath}/${meetingId}/participants/${userId}/status`,
      payload
    );
    return response.data;
  },

  async submitMeetingOverallEvaluation(
    meetingId: number,
    payload: SubmitMeetingOverallEvaluationPayload
  ): Promise<ApiResponse<MeetingOverallEvaluationResponse>> {
    const response = await axiosInstance.post<ApiResponse<MeetingOverallEvaluationResponse>>(
      `/${this.subPath}/${meetingId}/evaluations/overall`,
      payload
    );
    return response.data;
  },

  async getMeetingOverallEvaluation(
    meetingId: number
  ): Promise<ApiResponse<MeetingOverallEvaluationResponse | null>> {
    const response = await axiosInstance.get<ApiResponse<MeetingOverallEvaluationResponse | null>>(
      `/${this.subPath}/${meetingId}/evaluations/overall`
    );
    return response.data;
  },

  async submitTrainerEvaluation(
    meetingId: number,
    payload: TrainerSubmitEvaluationPayload
  ): Promise<ApiResponse<EvaluationResponse>> {
    const response = await axiosInstance.post<ApiResponse<EvaluationResponse>>(
      `/${this.subPath}/${meetingId}/evaluations/trainer`,
      payload
    );
    return response.data;
  },

  async submitTraineeEvaluation(
    meetingId: number,
    payload: TraineeSubmitEvaluationPayload
  ): Promise<ApiResponse<EvaluationResponse>> {
    const response = await axiosInstance.post<ApiResponse<EvaluationResponse>>(
      `/${this.subPath}/${meetingId}/evaluations/trainee`,
      payload
    );
    return response.data;
  },

  async getMeetingEvaluationSummary(meetingId: number): Promise<ApiResponse<MeetingEvaluationSummary>> {
    const response = await axiosInstance.get<ApiResponse<MeetingEvaluationSummary>>(
      `/${this.subPath}/${meetingId}/evaluations/summary`
    );
    return response.data;
  },

  async getSeatAvailability(meetingId: number): Promise<ApiResponse<MeetingSeatAvailabilityDto>> {
    const response = await axiosInstance.get<ApiResponse<MeetingSeatAvailabilityDto>>(
      `/${this.subPath}/${meetingId}/seats`
    );
    return response.data;
  },

  async getAvailableSeats(fromDate?: string): Promise<ApiResponse<MeetingSeatAvailabilityDto[]>> {
    const response = await axiosInstance.get<ApiResponse<MeetingSeatAvailabilityDto[]>>(
      `/${this.subPath}/available-seats`,
      { params: fromDate ? { from_date: fromDate } : undefined }
    );
    return response.data;
  },
};
