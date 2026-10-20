import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
    Notification,
    NotificationFilterParams,
    UnreadCountResponse,
} from '../types/notification.types';

export const notificationService = {
    getMyNotifications: async (
        params?: NotificationFilterParams
    ): Promise<ApiResponse<Notification[]>> => {
        const response = await axiosInstance.get<ApiResponse<Notification[]>>(
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

    markAsRead: async (id: number): Promise<ApiResponse<Notification>> => {
        const response = await axiosInstance.patch<ApiResponse<Notification>>(
            `/notifications/${id}/read`
        );
        return response.data;
    },

    markAllAsRead: async (): Promise<ApiResponse<number>> => {
        const response = await axiosInstance.post<ApiResponse<number>>(
            '/notifications/read-all'
        );
        return response.data;
    },
};
