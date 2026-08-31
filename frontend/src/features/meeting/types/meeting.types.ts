import { z } from 'zod';

export const ParticipantStatus = {
  NOT_JOINED: 'NOT_JOINED',
  JOINED: 'JOINED',
  COMPLETED: 'COMPLETED',
} as const;

export type ParticipantStatus = typeof ParticipantStatus[keyof typeof ParticipantStatus];
export const participantStatusSchema = z.enum(['NOT_JOINED', 'JOINED', 'COMPLETED']);

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

export const meetingResponseSchema = z.object({
  id: z.number(),
  title: z.string(),
  content: z.string().optional(),
  start_time: z.string(),
  end_time: z.string(),
  require_check_in: z.boolean(),
  participants: z.array(participantResponseSchema).default([]),
  created_at: z.string(),
  updated_at: z.string(),
});
export type MeetingResponse = z.infer<typeof meetingResponseSchema>;

export const meetingCreateSchema = z.object({
  title: z.string().min(1, 'Vui lòng nhập tiêu đề cuộc họp'),
  content: z.string().optional(),
  start_time: z.string().min(1, 'Vui lòng chọn thời gian bắt đầu'),
  end_time: z.string().min(1, 'Vui lòng chọn thời gian kết thúc'),
  require_check_in: z.boolean().optional(),
  team_ids: z.array(z.number()).optional(),
  user_ids: z.array(z.number()).optional(),
});
export type MeetingCreate = z.infer<typeof meetingCreateSchema>;
export type CreateMeetingFormValues = MeetingCreate;

export const meetingUpdateSchema = meetingCreateSchema.partial();
export type MeetingUpdate = z.infer<typeof meetingUpdateSchema>;
export type UpdateMeetingFormValues = MeetingUpdate;
