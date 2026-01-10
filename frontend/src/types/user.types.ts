export type UserStatus = 'active' | 'inactive';

export interface UserResponse {
  id: number;
  name: string;
  email: string;
  phone_number: string | null;
  status: UserStatus;
  role_id: number | null;
  role_name: string | null;
  permissions: string[];
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  phone_number?: string;
  status?: UserStatus;
  role_id?: number;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  password?: string;
  phone_number?: string;
  status?: UserStatus;
  role_id?: number;
}
