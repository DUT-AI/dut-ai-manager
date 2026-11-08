import type { Schema } from '@/types/api';

export const ParticipantStatus = {
  NOT_JOINED: 'NOT_JOINED',
  JOINED: 'JOINED',
  LATE_EXCUSED: 'LATE_EXCUSED',
  LATE_UNEXCUSED: 'LATE_UNEXCUSED',
  ABSENT_EXCUSED: 'ABSENT_EXCUSED',
  ABSENT_UNEXCUSED: 'ABSENT_UNEXCUSED',
  COMPLETED: 'COMPLETED',
} as const;

export type ParticipantStatus = typeof ParticipantStatus[keyof typeof ParticipantStatus];

export const ParticipantRole = {
  TRAINER: 'TRAINER',
  TRAINEE: 'TRAINEE',
} as const;

export type ParticipantRole = typeof ParticipantRole[keyof typeof ParticipantRole];

export interface UpdateParticipantStatusPayload {
  status: ParticipantStatus;
  check_in_at?: string | null;
  check_out_at?: string | null;
}

export type ParticipantResponse = Schema<'ParticipantResponse'>;
export type UserRef = Schema<'UserRef'>;
export type MeetingResponse = Schema<'MeetingResponse'>;
export type MeetingDetailResponse = Schema<'MeetingDetailResponse'>;

export type MeetingCreate = Schema<'MeetingCreate'>;
export type CreateMeetingFormValues = MeetingCreate;

export type MeetingUpdate = Schema<'MeetingUpdate'>;
export type UpdateMeetingFormValues = MeetingUpdate;

// ==========================================
// EVALUATION TYPES
// ==========================================

export interface EvaluationScoreItem {
  criteria_code: string;
  criteria_name: string;
  criteria_description: string;
  score: number;
}

export interface EvaluationScoreItemSubmit {
  criteria_code: string;
  score: number;
}

export interface SubmitMeetingOverallEvaluationPayload {
  scores: EvaluationScoreItemSubmit[];
  general_feedback?: string;
}

export interface MeetingOverallEvaluationResponse {
  id: number;
  meeting_id: number;
  trainer_id: number;
  scores: EvaluationScoreItem[];
  average_score: number;
  general_feedback?: string | null;
  trainer?: UserRef | null;
  created_at: string;
}

export interface TraineeSubmitEvaluationPayload {
  target_user_id: number;
  is_anonymous?: boolean;
  scores: EvaluationScoreItemSubmit[];
  feedback_text?: string;
}

export interface EvaluationResponse {
  id: number;
  meeting_id: number;
  reviewer_id?: number | null;
  target_user_id: number;
  evaluation_type: 'TRAINER_TO_TRAINEE' | 'TRAINEE_TO_TRAINER';
  is_anonymous: boolean;
  scores: EvaluationScoreItem[];
  average_score: number;
  feedback_text?: string | null;
  reviewer?: UserRef | null;
  target_user?: UserRef | null;
  created_at: string;
}

export interface CriteriaBreakdown {
  criteria_code: string;
  criteria_name: string;
  criteria_description: string;
  average_score: number;
  count: number;
  evaluation_type?: 'TRAINER_TO_TRAINEE' | 'TRAINEE_TO_TRAINER' | string;
}

export interface MeetingEvaluationSummary {
  meeting_id: number;
  total_evaluations: number;
  overall_average_score: number;
  criteria_breakdown: CriteriaBreakdown[];
  evaluations: EvaluationResponse[];
  total_trainer_evaluations?: number;
  total_trainee_evaluations?: number;
  trainer_average_score?: number | null;
  trainee_average_score?: number | null;
  my_evaluation?: EvaluationResponse | null;
  overall_evaluation?: MeetingOverallEvaluationResponse | null;
}

export interface MeetingSeatAvailabilityDto {
  id: number;
  title: string;
  start_time: string;
  end_time: string;
  max_seats: number;
  occupied_seats: number;
  available_seats: number;
  is_full: boolean;
}


