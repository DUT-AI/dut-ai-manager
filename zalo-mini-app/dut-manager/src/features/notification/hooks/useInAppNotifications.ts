import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'zmp-ui';
import { notificationService } from '@/services/api/notification.service';
import type {
  NotificationItem,
  NotificationCategory,
} from '@/types/notification.types';

export const useInAppNotifications = (isAuthenticated: boolean = true) => {
  const queryClient = useQueryClient();
  const { openSnackbar } = useSnackbar();

  const [category, setCategory] = useState<NotificationCategory | 'ALL'>('ALL');
  const [filterRead, setFilterRead] = useState<'ALL' | 'UNREAD' | 'READ'>('ALL');
  const [page, setPage] = useState<number>(1);
  const pageSize = 20;

  // 1. Unread count query (polls every 30s)
  const { data: unreadData, refetch: refetchUnreadCount } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: async () => {
      const res = await notificationService.getUnreadCount();
      return res.data?.unread_count ?? 0;
    },
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });

  const unreadCount = unreadData ?? 0;

  // 2. Notifications list query
  const {
    data: listResponse,
    isLoading,
    isFetching,
    refetch: refetchList,
  } = useQuery({
    queryKey: ['notifications-my', category, filterRead, page, pageSize],
    queryFn: async () => {
      const catParam = category === 'ALL' ? undefined : category;
      const readParam =
        filterRead === 'ALL' ? undefined : filterRead === 'READ' ? true : false;

      return await notificationService.getMyNotifications({
        category: catParam,
        is_read: readParam,
        page,
        page_size: pageSize,
      });
    },
    enabled: isAuthenticated,
  });

  const notifications: NotificationItem[] = listResponse?.data || [];
  const pagination = listResponse?.pagination || {
    page: 1,
    page_size: pageSize,
    total: 0,
    total_pages: 1,
    has_next: false,
  };

  // 3. Mark single notification as read
  const markAsReadMutation = useMutation({
    mutationFn: (id: number) => notificationService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications-my'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
  });

  // 4. Mark all as read
  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      openSnackbar({ text: 'Đã đánh dấu tất cả là đã đọc', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['notifications-my'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
    onError: () => {
      openSnackbar({ text: 'Không thể đánh dấu tất cả đã đọc', type: 'error' });
    },
  });

  // 5. Delete notification
  const deleteMutation = useMutation({
    mutationFn: (id: number) => notificationService.deleteNotification(id),
    onSuccess: () => {
      openSnackbar({ text: 'Đã xóa thông báo', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['notifications-my'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
  });

  const handleMarkAsRead = (id: number) => {
    markAsReadMutation.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    if (unreadCount === 0) return;
    markAllAsReadMutation.mutate();
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const refreshAll = () => {
    refetchList();
    refetchUnreadCount();
  };

  return {
    notifications,
    pagination,
    unreadCount,
    isLoading: isLoading || isFetching,
    category,
    setCategory,
    filterRead,
    setFilterRead,
    page,
    setPage,
    handleMarkAsRead,
    handleMarkAllAsRead,
    handleDelete,
    refreshAll,
    isMarkingAll: markAllAsReadMutation.isPending,
  };
};
