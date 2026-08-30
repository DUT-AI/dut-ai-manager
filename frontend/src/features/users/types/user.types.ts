import { z } from 'zod';

export const UserRole = {
  ADMIN: 'admin',
  MEMBER: 'member',
  LEADER: 'leader',
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const UserStatus = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE',
} as const;
export type UserStatus = (typeof UserStatus)[keyof typeof UserStatus];

// User Response Schema & Type
export const userResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  phone_number: z.string().nullable().optional(),
  status: z.enum(['ACTIVE', 'INACTIVE']).or(z.string()),
  discord_id: z.string().nullable().optional(),
  zalo_id: z.string().nullable().optional(),
  check_in_card_code: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  role_names: z.array(z.string()).default([]),
  permission_names: z.array(z.string()).default([]),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});
export type UserResponse = z.infer<typeof userResponseSchema>;

// Create User Schema & Type
export const createUserSchema = z.object({
  name: z.string().min(1, 'Vui lòng nhập tên thành viên'),
  email: z.string().email('Email không hợp lệ'),
  phone_number: z.string().optional().nullable(),
  role_ids: z.array(z.number()).optional(),
  status: z.enum(['ACTIVE', 'INACTIVE']).optional(),
  discord_id: z.string().optional().nullable(),
  check_in_card_code: z.string().max(64).optional().nullable(),
});
export type UserCreate = z.infer<typeof createUserSchema>;
export type CreateUserFormValues = UserCreate;

// Update User Schema & Type
export const updateUserSchema = createUserSchema.partial();
export type UserUpdate = z.infer<typeof updateUserSchema>;
export type UpdateUserFormValues = UserUpdate;

// User Settings Update Schema & Type
export const userSettingsUpdateSchema = z.object({
  discord_id: z.string().optional().nullable(),
  check_in_card_code: z.string().max(64).optional().nullable(),
});
export type UserSettingsUpdate = z.infer<typeof userSettingsUpdateSchema>;

// Change Password Schema & Type
export const changePasswordSchema = z.object({
  old_password: z.string().min(1, 'Vui lòng nhập mật khẩu cũ'),
  new_password: z.string().min(6, 'Mật khẩu mới tối thiểu 6 ký tự'),
  confirm_password: z.string().min(1, 'Vui lòng xác nhận mật khẩu mới'),
}).refine(data => data.new_password === data.confirm_password, {
  message: 'Mật khẩu mới không khớp',
  path: ['confirm_password'],
});
export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

export interface UserImportResult {
  total: number;
  success_count: number;
  error_count: number;
  errors?: string[];
}
