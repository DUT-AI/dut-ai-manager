import type { Schema } from '@/types/api';

export type LoginRequest = Schema<'LoginRequest'>;
export type TokenResponse = Schema<'TokenResponse'>;
export type RefreshTokenRequest = Schema<'RefreshTokenRequest'>;
export type ChangePasswordRequest = Schema<'ChangePasswordRequest'>;

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  phone_number?: string;
}
