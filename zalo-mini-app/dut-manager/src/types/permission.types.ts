import { z } from 'zod';

export const RequestCategory = {
  ABSENCE: 'ABSENCE',   // Xin vắng sinh hoạt / họp
  POSTPONE: 'POSTPONE', // Xin hoãn bài tập
  LATE: 'LATE',         // Xin đi trễ
  OTHER: 'OTHER',       // Khác
} as const;

export type RequestCategory = (typeof RequestCategory)[keyof typeof RequestCategory];
export const requestCategorySchema = z.enum(['ABSENCE', 'POSTPONE', 'LATE', 'OTHER']);

export const CATEGORY_LABELS: Record<RequestCategory, { label: string; color: string; bg: string }> = {
  ABSENCE: { label: 'Vắng sinh hoạt', color: 'text-rose-600', bg: 'bg-rose-50 border-rose-200' },
  POSTPONE: { label: 'Hoãn bài tập', color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
  LATE: { label: 'Đi trễ', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' },
  OTHER: { label: 'Lý do khác', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' },
};

export const userRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  avatar_url: z.string().nullable().optional(),
});
export type UserRef = z.infer<typeof userRefSchema>;

export const permissionMeetingRefSchema = z.object({
  id: z.number(),
  title: z.string(),
  start_time: z.string(),
});
export type PermissionMeetingRef = z.infer<typeof permissionMeetingRefSchema>;

export const permissionHomeworkRefSchema = z.object({
  id: z.number(),
  title: z.string(),
  deadline: z.string(),
});
export type PermissionHomeworkRef = z.infer<typeof permissionHomeworkRefSchema>;

export const permissionRequestCreateSchema = z.object({
  category: z.string().min(1, 'Vui lòng chọn loại đơn'),
  note: z.string().min(1, 'Vui lòng nhập lý do/ghi chú'),
  start_time: z.string().optional(),
  homework_id: z.number().nullable().optional(),
  meeting_id: z.number().nullable().optional(),
});
export type PermissionRequestCreate = z.infer<typeof permissionRequestCreateSchema>;

export const permissionRequestUpdateSchema = permissionRequestCreateSchema.partial();
export type PermissionRequestUpdate = z.infer<typeof permissionRequestUpdateSchema>;

export const permissionRequestResponseSchema = z.object({
  id: z.number(),
  category: z.string(),
  note: z.string(),
  start_time: z.string().nullable().optional(),
  homework_id: z.number().nullable().optional(),
  meeting_id: z.number().nullable().optional(),
  created_by: z.number().nullable().optional(),
  updated_by: z.number().nullable().optional(),
  owner: userRefSchema.nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  creator: userRefSchema.nullable().optional(),
  updater: userRefSchema.nullable().optional(),
  homework: permissionHomeworkRefSchema.nullable().optional(),
  meeting: permissionMeetingRefSchema.nullable().optional(),
});
export type PermissionRequestResponse = z.infer<typeof permissionRequestResponseSchema>;
