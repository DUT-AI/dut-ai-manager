import type { Schema } from '@/types/api';

export type ViolationOwner = Schema<'UserRef'>;
export type ViolationResponse = Schema<'app__violation__schemas__ViolationResponse'>;

export type ViolationCreate = Schema<'ViolationCreate'>;
export type CreateViolationFormValues = ViolationCreate;

export type ViolationUpdate = Schema<'ViolationUpdate'>;
export type UpdateViolationFormValues = ViolationUpdate;
