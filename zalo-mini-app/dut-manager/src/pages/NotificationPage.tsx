import React, { useState } from 'react';
import { Page, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import {
  useInAppNotifications,
  NotificationCard,
  NotificationFilterBar,
  NotificationDetailModal,
} from '@/features/notification';
import type { NotificationItem } from '@/types/notification.types';

const NotificationPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const {
    notifications,
    pagination,
    unreadCount,
    isLoading,
    category,
    setCategory,
    filterRead,
    setFilterRead,
    handleMarkAsRead,
    handleMarkAllAsRead,
    handleDelete,
    refreshAll,
    isMarkingAll,
  } = useInAppNotifications(isAuthenticated);

  const [selectedNotification, setSelectedNotification] =
    useState<NotificationItem | null>(null);

  const handleCardClick = (item: NotificationItem) => {
    if (!item.is_read) {
      handleMarkAsRead(item.id);
    }
    setSelectedNotification(item);
  };

  return (
    <Page className="bg-[#f8fafc] flex flex-col min-h-screen">
      <Header title="Thông báo" showBack={false} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-3 pb-24">
        {/* 1. Header Banner Overview */}
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
              <Icon icon="zi-notif" size={22} />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-base text-gray-900">Thông báo của tôi</h2>
                {unreadCount > 0 && (
                  <span className="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full animate-pulse">
                    {unreadCount > 99 ? '99+' : unreadCount} mới
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 line-clamp-1">
                Nhắc nhở bài tập, lịch họp, trực nhật & thông báo
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={refreshAll}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 active:bg-gray-200 transition-colors shrink-0"
            title="Làm mới"
          >
            <Icon icon="zi-retry" size={16} />
          </button>
        </div>

        {/* 2. Filter Bar */}
        <div className="bg-white p-3 rounded-2xl border border-gray-100 shadow-sm">
          <NotificationFilterBar
            activeCategory={category}
            onChangeCategory={setCategory}
            activeFilterRead={filterRead}
            onChangeFilterRead={setFilterRead}
            unreadCount={unreadCount}
            onMarkAllAsRead={handleMarkAllAsRead}
            isMarkingAll={isMarkingAll}
          />
        </div>

        {/* 3. Notification List */}
        <div className="flex flex-col gap-2.5">
          {isLoading && notifications.length === 0 ? (
            /* Skeleton Loading */
            <div className="flex flex-col gap-2.5">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="bg-white p-4 rounded-2xl border border-gray-100 animate-pulse flex gap-3"
                >
                  <div className="w-10 h-10 bg-gray-200 rounded-2xl shrink-0" />
                  <div className="flex-1 flex flex-col gap-2">
                    <div className="h-3.5 bg-gray-200 rounded w-1/3" />
                    <div className="h-3 bg-gray-200 rounded w-3/4" />
                    <div className="h-2.5 bg-gray-200 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : notifications.length === 0 ? (
            /* Empty State */
            <div className="bg-white rounded-2xl p-8 border border-gray-100 text-center flex flex-col items-center gap-3 mt-2">
              <div className="w-14 h-14 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center">
                <Icon icon="zi-notif" size={28} />
              </div>
              <div className="flex flex-col gap-1">
                <p className="font-bold text-sm text-gray-800">
                  {filterRead === 'UNREAD'
                    ? 'Không có thông báo chưa đọc nào'
                    : 'Chưa có thông báo nào'}
                </p>
                <p className="text-xs text-gray-400 max-w-xs">
                  {filterRead === 'UNREAD'
                    ? 'Tuyệt vời! Bạn đã đọc hết tất cả thông báo.'
                    : 'Các thông báo và nhắc việc mới sẽ xuất hiện tại đây.'}
                </p>
              </div>
            </div>
          ) : (
            /* Notifications Cards */
            notifications.map((item) => (
              <NotificationCard
                key={item.id}
                notification={item}
                onClick={handleCardClick}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>
      </div>

      {/* 4. Notification Detail Modal */}
      <NotificationDetailModal
        notification={selectedNotification}
        onClose={() => setSelectedNotification(null)}
        onDelete={handleDelete}
      />
    </Page>
  );
};

export default NotificationPage;
