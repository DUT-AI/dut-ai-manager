import type { Schema } from '@/types/api';

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
export type UserStatus = Schema<'UserStatus'>;

// User Response Type from OpenAPI
export type UserResponse = Schema<'UserResponse'>;

// Create User Type
export type UserCreate = Schema<'UserCreate'>;
export type CreateUserFormValues = UserCreate;

// Update User Type
export type UserUpdate = Schema<'UserUpdate'>;
export type UpdateUserFormValues = UserUpdate;

// User Settings Update Type
export type UserSettingsUpdate = Schema<'UserSettingsUpdate'>;

// Change Password Type
export type ChangePasswordFormValues = Schema<'ChangePasswordRequest'>;

export type UserImportResult = Schema<'UserImportResult'>;
export type UserOptionDto = Schema<'UserOptionDto'>;
