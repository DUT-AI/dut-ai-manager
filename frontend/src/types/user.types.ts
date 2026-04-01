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
  discord_id: string | null;
  zalo_id: string | null;
  avatar_url: string | null;
  /** API không trả về mã thật; chỉ biết đã lưu hay chưa */
  check_in_card_code_configured?: boolean;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  phone_number?: string;
  status?: UserStatus;
  role_id?: number;
  discord_id?: string;
  zalo_id?: string;
  avatar_url?: string;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  password?: string;
  phone_number?: string;
  status?: UserStatus;
  role_id?: number;
  discord_id?: string;
  zalo_id?: string;
  avatar_url?: string;
}

export interface UserSettingsUpdate {
  discord_id?: string;
  zalo_id?: string;
  avatar_url?: string;
  check_in_card_code?: string;
}
