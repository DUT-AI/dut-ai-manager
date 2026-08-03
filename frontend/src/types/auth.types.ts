import { z } from 'zod';

export const loginRequestSchema = z.object({
  email: z.string().email('Email không hợp lệ'),
  password: z.string().min(1, 'Vui lòng nhập mật khẩu'),
});
export type LoginRequest = z.infer<typeof loginRequestSchema>;

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
});
export type TokenResponse = z.infer<typeof tokenResponseSchema>;

export const refreshTokenRequestSchema = z.object({
  refresh_token: z.string(),
});
export type RefreshTokenRequest = z.infer<typeof refreshTokenRequestSchema>;

export const registerRequestSchema = z.object({
  name: z.string().min(1, 'Vui lòng nhập họ tên'),
  email: z.string().email('Email không hợp lệ'),
  password: z.string().min(6, 'Mật khẩu tối thiểu 6 ký tự'),
  phone_number: z.string().optional(),
});
export type RegisterRequest = z.infer<typeof registerRequestSchema>;

export const changePasswordRequestSchema = z.object({
  old_password: z.string().min(1, 'Vui lòng nhập mật khẩu hiện tại'),
  new_password: z.string().min(6, 'Mật khẩu mới tối thiểu 6 ký tự'),
  confirm_password: z.string().min(1, 'Vui lòng xác nhận mật khẩu mới'),
}).refine(data => data.new_password === data.confirm_password, {
  message: 'Mật khẩu mới không khớp',
  path: ['confirm_password'],
});
export type ChangePasswordRequest = z.infer<typeof changePasswordRequestSchema>;
