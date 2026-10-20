import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { notificationService } from '../services/notification.service';
import type {
    Notification,
    NotificationCategory,
} from '../types/notification.types';

export const useInAppNotifications = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState<number>(0);
    const [loading, setLoading] = useState<boolean>(false);
    const [total, setTotal] = useState<number>(0);

    // Filter states
    const [page, setPage] = useState<number>(1);
    const [pageSize, setPageSize] = useState<number>(20);
    const [category, setCategory] = useState<NotificationCategory | undefined>(undefined);
    const [isRead, setIsRead] = useState<boolean | undefined>(undefined);

    const fetchUnreadCount = useCallback(async () => {
        try {
            const res = await notificationService.getUnreadCount();
            if (res?.data?.unread_count !== undefined) {
                setUnreadCount(res.data.unread_count);
            }
        } catch {
            // Im lặng nếu lỗi mạng nền
        }
    }, []);

    const fetchNotifications = useCallback(async () => {
        setLoading(true);
        try {
            const res = await notificationService.getMyNotifications({
                category,
                is_read: isRead,
                page,
                page_size: pageSize,
            });
            if (res?.data) {
                setNotifications(res.data);
                if (res.meta?.total !== undefined) {
                    setTotal(res.meta.total);
                }
            }
        } catch {
            message.error('Không thể tải danh sách thông báo');
        } finally {
            setLoading(false);
        }
    }, [category, isRead, page, pageSize]);

    useEffect(() => {
        fetchNotifications();
    }, [fetchNotifications]);

    useEffect(() => {
        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 30000); // Poll mỗi 30s
        return () => clearInterval(interval);
    }, [fetchUnreadCount]);

    const handleMarkAsRead = async (id: number) => {
        try {
            await notificationService.markAsRead(id);
            setNotifications((prev) =>
                prev.map((item) =>
                    item.id === id ? { ...item, is_read: true } : item
                )
            );
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch {
            message.error('Thao tác thất bại');
        }
    };

    const handleMarkAllAsRead = async () => {
        try {
            await notificationService.markAllAsRead();
            message.success('Đã đánh dấu tất cả thông báo là đã đọc');
            setNotifications((prev) =>
                prev.map((item) => ({ ...item, is_read: true }))
            );
            setUnreadCount(0);
        } catch {
            message.error('Không thể đánh dấu tất cả đã đọc');
        }
    };

    return {
        notifications,
        unreadCount,
        loading,
        total,
        page,
        setPage,
        pageSize,
        setPageSize,
        category,
        setCategory,
        isRead,
        setIsRead,
        refresh: fetchNotifications,
        refreshCount: fetchUnreadCount,
        markAsRead: handleMarkAsRead,
        markAllAsRead: handleMarkAllAsRead,
    };
};
