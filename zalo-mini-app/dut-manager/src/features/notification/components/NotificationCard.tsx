import React from 'react';
import { Icon } from 'zmp-ui';
import type {
  NotificationItem,
  NotificationCategory,
  NotificationLevel,
} from '@/types/notification.types';

interface NotificationCardProps {
  notification: NotificationItem;
  onClick: (item: NotificationItem) => void;
  onDelete?: (id: number) => void;
}

const formatNotificationTime = (isoString: string): string => {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '';
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;

    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    return `${hours}:${mins} ${day}/${month}`;
  } catch {
    return '';
  }
};

const categoryConfig: Record<
  NotificationCategory,
  { label: string; bg: string; text: string; icon: string }
> = {
  HOMEWORK: {
    label: 'Bài tập',
    bg: 'bg-blue-50 border-blue-200',
    text: 'text-blue-600',
    icon: 'zi-file',
  },
  MEETING: {
    label: 'Lịch họp',
    bg: 'bg-purple-50 border-purple-200',
    text: 'text-purple-600',
    icon: 'zi-calendar',
  },
  DUTY: {
    label: 'Trực nhật',
    bg: 'bg-teal-50 border-teal-200',
    text: 'text-teal-600',
    icon: 'zi-check-circle',
  },
  SYSTEM: {
    label: 'Hệ thống',
    bg: 'bg-gray-100 border-gray-200',
    text: 'text-gray-600',
    icon: 'zi-notif',
  },
};

const levelConfig: Record<
  NotificationLevel,
  { label: string; badgeBg: string; badgeText: string }
> = {
  INFO: {
    label: 'Thông tin',
    badgeBg: 'bg-blue-50',
    badgeText: 'text-blue-700',
  },
  WARNING: {
    label: 'Cảnh báo',
    badgeBg: 'bg-amber-50',
    badgeText: 'text-amber-700',
  },
  CRITICAL: {
    label: 'Khẩn cấp',
    badgeBg: 'bg-rose-50',
    badgeText: 'text-rose-700',
  },
};

export const NotificationCard: React.FC<NotificationCardProps> = ({
  notification,
  onClick,
  onDelete,
}) => {
  const cat = categoryConfig[notification.category] || categoryConfig.SYSTEM;
  const lvl = levelConfig[notification.level] || levelConfig.INFO;
  const timeFormatted = formatNotificationTime(notification.created_at);

  return (
    <div
      onClick={() => onClick(notification)}
      className={`relative p-3.5 rounded-2xl border transition-all cursor-pointer active:scale-[0.99] flex gap-3 ${
        notification.is_read
          ? 'bg-white border-gray-100 opacity-80 hover:opacity-100'
          : 'bg-blue-50/40 border-blue-100 shadow-2xs'
      }`}
    >
      {/* Category Icon */}
      <div
        className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border ${cat.bg} ${cat.text}`}
      >
        <Icon icon={cat.icon as any} size={20} />
      </div>

      {/* Main Content */}
      <div className="flex-1 min-w-0 flex flex-col gap-1">
        <div className="flex items-center justify-between gap-2">
          {/* Tags */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cat.bg} ${cat.text}`}
            >
              {cat.label}
            </span>
            {notification.level !== 'INFO' && (
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${lvl.badgeBg} ${lvl.badgeText}`}
              >
                {lvl.label}
              </span>
            )}
          </div>

          {/* Time & Unread dot */}
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="text-[11px] text-gray-400 font-medium">
              {timeFormatted}
            </span>
            {!notification.is_read && (
              <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0" />
            )}
          </div>
        </div>

        {/* Title */}
        <h4
          className={`text-xs line-clamp-1 ${
            notification.is_read
              ? 'text-gray-700 font-semibold'
              : 'text-gray-900 font-bold'
          }`}
        >
          {notification.title}
        </h4>

        {/* Content Excerpt */}
        <p className="text-[11px] text-gray-500 line-clamp-2 leading-relaxed">
          {notification.content}
        </p>

        {/* Action Link Indicator */}
        {notification.action_url && (
          <div className="flex items-center gap-1 text-[11px] text-blue-600 font-medium mt-0.5">
            <span>Xem chi tiết</span>
            <Icon icon="zi-chevron-right" size={12} />
          </div>
        )}
      </div>
    </div>
  );
};
