import { z } from 'zod';

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
export const participantStatusSchema = z.enum([
  'NOT_JOINED',
  'JOINED',
  'LATE_EXCUSED',
  'LATE_UNEXCUSED',
  'ABSENT_EXCUSED',
  'ABSENT_UNEXCUSED',
  'COMPLETED',
]);

export interface UpdateParticipantStatusPayload {
  status: ParticipantStatus;
  check_in_at?: string | null;
  check_out_at?: string | null;
}

export const participantResponseSchema = z.object({
  id: z.number(),
  meeting_id: z.number(),
  user_id: z.number(),
  user_name: z.string().optional(),
  user_avatar_url: z.string().nullable().optional(),
  check_in_at: z.string().nullable().optional(),
  check_out_at: z.string().nullable().optional(),
  status: participantStatusSchema,
  link_image: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type ParticipantResponse = z.infer<typeof participantResponseSchema>;

export const userRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  avatar_url: z.string().nullable().optional(),
});
export type UserRef = z.infer<typeof userRefSchema>;

export const meetingResponseSchema = z.object({
  id: z.number(),
  title: z.string(),
  content: z.string().optional(),
  start_time: z.string(),
  end_time: z.string(),
  require_check_in: z.boolean(),
  enable_evaluation: z.boolean().default(false),
  evaluation_deadline: z.string().nullable().optional(),
  created_by: z.number().nullable().optional(),
  trainer: userRefSchema.default({ id: 0, name: 'Trainer' }),
  created_at: z.string(),
  updated_at: z.string(),
});
export type MeetingResponse = z.infer<typeof meetingResponseSchema>;

export const meetingDetailResponseSchema = meetingResponseSchema.extend({
  participants: z.array(participantResponseSchema).default([]),
});
export type MeetingDetailResponse = z.infer<typeof meetingDetailResponseSchema>;

export const meetingCreateSchema = z.object({
  title: z.string().min(1, 'Vui lòng nhập tiêu đề cuộc họp'),
  content: z.string().optional(),
  start_time: z.string().min(1, 'Vui lòng chọn thời gian bắt đầu'),
  end_time: z.string().min(1, 'Vui lòng chọn thời gian kết thúc'),
  require_check_in: z.boolean().optional(),
  enable_evaluation: z.boolean().optional(),
  user_ids: z.array(z.number()).optional(),
});
export type MeetingCreate = z.infer<typeof meetingCreateSchema>;
export type CreateMeetingFormValues = MeetingCreate;

export const meetingUpdateSchema = meetingCreateSchema.partial();
export type MeetingUpdate = z.infer<typeof meetingUpdateSchema>;
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

export interface TrainerSubmitEvaluationPayload {
  target_user_id: number;
  scores: EvaluationScoreItemSubmit[];
  feedback_text?: string;
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
}

export interface MeetingEvaluationSummary {
  meeting_id: number;
  total_evaluations: number;
  overall_average_score: number;
  criteria_breakdown: CriteriaBreakdown[];
  evaluations: EvaluationResponse[];
}
