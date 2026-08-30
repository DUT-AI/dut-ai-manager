import { z } from 'zod';

export const userRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
});
export type UserRef = z.infer<typeof userRefSchema>;

export const permissionRequestCreateSchema = z.object({
  category: z.string().min(1, 'Vui lòng chọn loại đơn'),
  note: z.string().min(1, 'Vui lòng nhập lý do/ghi chú'),
  start_time: z.string().optional(),
  homework_id: z.number().optional(),
  meeting_id: z.number().optional(),
});
export type PermissionRequestCreate = z.infer<typeof permissionRequestCreateSchema>;
export type PermissionRequestUpdate = Partial<PermissionRequestCreate>;

// Aliases for legacy code
export const permissionCreateSchema = permissionRequestCreateSchema;
export type PermissionCreate = PermissionRequestCreate;
export type PermissionUpdate = PermissionRequestUpdate;

export const bonusPointCreateSchema = z.object({
  user_ids: z.array(z.number()).min(1, 'Vui lòng chọn thành viên'),
  points: z.number().min(1, 'Điểm phải lớn hơn 0'),
  reason: z.string().min(1, 'Vui lòng nhập lý do'),
  date: z.string(),
});
export type BonusPointCreate = z.infer<typeof bonusPointCreateSchema>;
export type BonusPointUpdate = Partial<BonusPointCreate>;

export const violationCreateSchema = z.object({
  user_ids: z.array(z.number()).min(1, 'Vui lòng chọn thành viên'),
  reason: z.string().min(1, 'Vui lòng nhập lý do'),
  date: z.string(),
});
export type ViolationCreate = z.infer<typeof violationCreateSchema>;
export type ViolationUpdate = Partial<ViolationCreate>;

export const bonusPointResponseSchema = z.object({
  id: z.number(),
  user_id: z.number().optional(),
  points: z.number(),
  reason: z.string(),
  date: z.string(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  owner: userRefSchema.nullable().optional(),
  creator: userRefSchema.nullable().optional(),
  updater: userRefSchema.nullable().optional(),
});
export type BonusPointResponse = z.infer<typeof bonusPointResponseSchema>;

export const permissionRequestResponseSchema = z.object({
  id: z.number(),
  category: z.string(),
  note: z.string(),
  start_time: z.string().optional(),
  homework_id: z.number().nullable().optional(),
  meeting_id: z.number().nullable().optional(),
  created_by: z.number().nullable().optional(),
  updated_by: z.number().nullable().optional(),
  owner: userRefSchema.nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  creator: userRefSchema.nullable().optional(),
  updater: userRefSchema.nullable().optional(),
  homework: z.any().optional(),
  meeting: z.any().optional(),
});
export type PermissionRequestResponse = z.infer<typeof permissionRequestResponseSchema>;

export const calendarEventSchema = z.object({
  id: z.string(),
  title: z.string(),
  date: z.string(),
  type: z.enum(['meeting', 'homework', 'violation', 'permission', 'bonus']),
  details: z.record(z.string(), z.unknown()).optional(),
});
export type CalendarEvent = z.infer<typeof calendarEventSchema>;

export interface DailySummaryResponse {
  permission_requests?: PermissionRequestResponse[];
  bonus_points?: BonusPointResponse[];
  violations?: any[];
  meetings?: any[];
}
