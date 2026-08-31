import { z } from 'zod';

export const violationOwnerSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  avatar_url: z.string().nullable().optional(),
});
export type ViolationOwner = z.infer<typeof violationOwnerSchema>;

export const violationResponseSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  reason: z.string(),
  date: z.string(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  owner: violationOwnerSchema.nullable().optional(),
  creator: violationOwnerSchema.nullable().optional(),
  updater: violationOwnerSchema.nullable().optional(),
});
export type ViolationResponse = z.infer<typeof violationResponseSchema>;

export const violationCreateSchema = z.object({
  user_ids: z.array(z.number()).min(1, 'Vui lòng chọn ít nhất 1 thành viên'),
  reason: z.string().min(1, 'Vui lòng nhập lý do vi phạm'),
  date: z.string(),
});
export type ViolationCreate = z.infer<typeof violationCreateSchema>;
export type CreateViolationFormValues = ViolationCreate;

export const violationUpdateSchema = z.object({
  reason: z.string().min(1, 'Vui lòng nhập lý do vi phạm'),
  date: z.string(),
});
export type ViolationUpdate = z.infer<typeof violationUpdateSchema>;
export type UpdateViolationFormValues = ViolationUpdate;
