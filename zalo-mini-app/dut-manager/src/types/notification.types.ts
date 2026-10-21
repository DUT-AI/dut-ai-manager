export type NotificationCategory = 'HOMEWORK' | 'DUTY' | 'MEETING' | 'SYSTEM';
export type NotificationLevel = 'INFO' | 'WARNING' | 'CRITICAL';

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  content: string;
  category: NotificationCategory;
  level: NotificationLevel;
  action_url?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationFilterParams {
  category?: NotificationCategory;
  is_read?: boolean;
  page?: number;
  page_size?: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}
