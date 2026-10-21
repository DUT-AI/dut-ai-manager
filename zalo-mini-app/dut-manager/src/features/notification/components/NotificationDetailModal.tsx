import React from 'react';
import { Modal, Button, Icon } from 'zmp-ui';
import { useNavigate } from 'react-router-dom';
import type { NotificationItem } from '@/types/notification.types';

interface NotificationDetailModalProps {
  notification: NotificationItem | null;
  onClose: () => void;
  onDelete?: (id: number) => void;
}

export const NotificationDetailModal: React.FC<NotificationDetailModalProps> = ({
  notification,
  onClose,
  onDelete,
}) => {
  const navigate = useNavigate();

  if (!notification) return null;

  const handleActionClick = () => {
    if (!notification.action_url) return;
    onClose();

    if (notification.action_url.startsWith('http')) {
      window.open(notification.action_url, '_blank');
    } else {
      navigate(notification.action_url);
    }
  };

  const formatFullTime = (isoString: string): string => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return '';
      const day = String(d.getDate()).padStart(2, '0');
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = d.getFullYear();
      const hours = String(d.getHours()).padStart(2, '0');
      const mins = String(d.getMinutes()).padStart(2, '0');
      return `${hours}:${mins} • ${day}/${month}/${year}`;
    } catch {
      return '';
    }
  };

  return (
    <Modal
      visible={notification !== null}
      title="Chi tiết thông báo"
      onClose={onClose}
      maskClosable
    >
      <div className="flex flex-col gap-3.5 py-1">
        {/* Meta badges & time */}
        <div className="flex items-center justify-between border-b border-gray-100 pb-2.5">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
              {notification.category}
            </span>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                notification.level === 'CRITICAL'
                  ? 'bg-rose-50 text-rose-700'
                  : notification.level === 'WARNING'
                  ? 'bg-amber-50 text-amber-700'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {notification.level}
            </span>
          </div>

          <span className="text-[11px] text-gray-400">
            {formatFullTime(notification.created_at)}
          </span>
        </div>

        {/* Title */}
        <h3 className="font-bold text-sm text-gray-900 leading-snug">
          {notification.title}
        </h3>

        {/* Full Content */}
        <div className="bg-gray-50/80 p-3.5 rounded-2xl border border-gray-100 text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">
          {notification.content}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2">
          {notification.action_url && (
            <Button
              className="flex-1 rounded-2xl bg-blue-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs"
              onClick={handleActionClick}
            >
              <span>Xem nội dung</span>
              <Icon icon="zi-chevron-right" size={14} />
            </Button>
          )}

          <Button
            type="neutral"
            className="rounded-2xl text-xs font-semibold"
            onClick={onClose}
          >
            Đóng
          </Button>
        </div>
      </div>
    </Modal>
  );
};
