import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  NotificationItem,
  NotificationFilterParams,
  UnreadCountResponse,
} from '@/types/notification.types';

export const notificationService = {
  getMyNotifications: async (
    params?: NotificationFilterParams
  ): Promise<ApiResponse<NotificationItem[]>> => {
    const response = await axiosInstance.get<ApiResponse<NotificationItem[]>>(
      '/notifications/my',
      { params }
    );
    return response.data;
  },

  getUnreadCount: async (): Promise<ApiResponse<UnreadCountResponse>> => {
    const response = await axiosInstance.get<ApiResponse<UnreadCountResponse>>(
      '/notifications/unread-count'
    );
    return response.data;
  },

  markAsRead: async (id: number): Promise<ApiResponse<NotificationItem>> => {
    const response = await axiosInstance.patch<ApiResponse<NotificationItem>>(
      `/notifications/${id}/read`
    );
    return response.data;
  },

  markAllAsRead: async (): Promise<ApiResponse<{ count: number }>> => {
    const response = await axiosInstance.post<ApiResponse<{ count: number }>>(
      '/notifications/read-all'
    );
    return response.data;
  },

  deleteNotification: async (id: number): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete<ApiResponse<null>>(
      `/notifications/${id}`
    );
    return response.data;
  },
};
