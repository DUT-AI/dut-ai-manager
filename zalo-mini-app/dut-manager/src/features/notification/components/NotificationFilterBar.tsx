import React from 'react';
import { Icon } from 'zmp-ui';
import type { NotificationCategory } from '@/types/notification.types';

interface NotificationFilterBarProps {
  activeCategory: NotificationCategory | 'ALL';
  onChangeCategory: (cat: NotificationCategory | 'ALL') => void;
  activeFilterRead: 'ALL' | 'UNREAD' | 'READ';
  onChangeFilterRead: (val: 'ALL' | 'UNREAD' | 'READ') => void;
  unreadCount: number;
  onMarkAllAsRead: () => void;
  isMarkingAll?: boolean;
}

const CATEGORY_TABS: Array<{ id: NotificationCategory | 'ALL'; label: string; icon?: string }> = [
  { id: 'ALL', label: 'Tất cả' },
  { id: 'HOMEWORK', label: 'Bài tập', icon: 'zi-file' },
  { id: 'MEETING', label: 'Lịch họp', icon: 'zi-calendar' },
  { id: 'DUTY', label: 'Trực nhật', icon: 'zi-check-circle' },
  { id: 'SYSTEM', label: 'Hệ thống', icon: 'zi-notif' },
];

export const NotificationFilterBar: React.FC<NotificationFilterBarProps> = ({
  activeCategory,
  onChangeCategory,
  activeFilterRead,
  onChangeFilterRead,
  unreadCount,
  onMarkAllAsRead,
  isMarkingAll,
}) => {
  return (
    <div className="flex flex-col gap-2.5">
      {/* Top Bar: Status switch & Mark all read */}
      <div className="flex items-center justify-between gap-2">
        {/* Read / Unread pills */}
        <div className="flex items-center p-0.5 bg-gray-100 rounded-xl">
          <button
            type="button"
            onClick={() => onChangeFilterRead('ALL')}
            className={`py-1 px-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeFilterRead === 'ALL'
                ? 'bg-white text-gray-900 shadow-2xs'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Tất cả
          </button>
          <button
            type="button"
            onClick={() => onChangeFilterRead('UNREAD')}
            className={`py-1 px-2.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
              activeFilterRead === 'UNREAD'
                ? 'bg-white text-blue-600 shadow-2xs'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            <span>Chưa đọc</span>
            {unreadCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[9px] flex items-center justify-center font-bold">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>
        </div>

        {/* Mark All As Read */}
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={onMarkAllAsRead}
            disabled={isMarkingAll}
            className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold text-blue-600 bg-blue-50/70 border border-blue-100 active:bg-blue-100 transition-colors"
          >
            <Icon icon="zi-check-circle-solid" size={14} />
            <span>Đọc tất cả</span>
          </button>
        )}
      </div>

      {/* Horizontal Category Filter Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
        {CATEGORY_TABS.map((tab) => {
          const isSelected = activeCategory === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChangeCategory(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition-all flex items-center gap-1.5 border ${
                isSelected
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
              }`}
            >
              {tab.icon && <Icon icon={tab.icon as any} size={14} />}
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
