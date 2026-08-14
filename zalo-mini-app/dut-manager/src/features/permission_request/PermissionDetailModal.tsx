import React from 'react';
import { Modal, Button } from 'zmp-ui';
import {
  RequestCategory,
  CATEGORY_LABELS,
  PermissionRequestResponse,
} from '@/types/permission.types';

interface PermissionDetailModalProps {
  item: PermissionRequestResponse | null;
  currentUserId?: number;
  hasUpdatePermission: boolean;
  onClose: () => void;
  onOpenEdit: (item: PermissionRequestResponse) => void;
  formatDate: (date?: string | null) => string;
}

export const PermissionDetailModal: React.FC<PermissionDetailModalProps> = ({
  item,
  currentUserId,
  hasUpdatePermission,
  onClose,
  onOpenEdit,
  formatDate,
}) => {
  if (!item) return null;

  const canEdit = currentUserId === item.owner?.id || hasUpdatePermission;
  const catLabel =
    CATEGORY_LABELS[item.category as RequestCategory]?.label || item.category;
  const catBg =
    CATEGORY_LABELS[item.category as RequestCategory]?.bg || 'bg-gray-100 border-gray-200';
  const catColor =
    CATEGORY_LABELS[item.category as RequestCategory]?.color || 'text-gray-700';

  return (
    <Modal
      visible={item !== null}
      title="Chi tiết Đơn xin phép"
      onClose={onClose}
      maskClosable
    >
      <div className="flex flex-col gap-4 py-2">
        <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-100">
          <span className="text-xs font-medium text-gray-500">Loại đơn:</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${catBg} ${catColor}`}>
            {catLabel}
          </span>
        </div>

        <div className="flex flex-col gap-1 text-xs">
          <span className="text-gray-400">Người làm đơn:</span>
          <span className="font-bold text-gray-800 text-sm">
            {item.owner?.name || (item.created_by ? `#${item.created_by}` : 'Thành viên Lab')}
          </span>
        </div>

        {item.meeting && (
          <div className="flex flex-col gap-1 text-xs">
            <span className="text-gray-400">Buổi họp / sinh hoạt:</span>
            <span className="font-bold text-blue-700 bg-blue-50 p-2.5 rounded-xl border border-blue-100">
              {item.meeting.title} ({formatDate(item.meeting.start_time)})
            </span>
          </div>
        )}

        {item.homework && (
          <div className="flex flex-col gap-1 text-xs">
            <span className="text-gray-400">Bài tập xin hoãn:</span>
            <span className="font-bold text-amber-700 bg-amber-50 p-2.5 rounded-xl border border-amber-100">
              {item.homework.title}
            </span>
          </div>
        )}

        {item.start_time && (
          <div className="flex flex-col gap-1 text-xs">
            <span className="text-gray-400">
              {item.category === 'LATE' ? 'Giờ có mặt:' : 'Hạn nộp mới / Bắt đầu:'}
            </span>
            <span className="font-semibold text-gray-800">
              {formatDate(item.start_time)}
            </span>
          </div>
        )}

        <div className="flex flex-col gap-1 text-xs">
          <span className="text-gray-400">Lý do:</span>
          <p className="text-sm text-gray-800 bg-gray-50 p-3 rounded-xl border border-gray-100 leading-relaxed font-medium">
            {item.note}
          </p>
        </div>

        <div className="flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-gray-100">
          <span>Ngày tạo:</span>
          <span>{formatDate(item.created_at)}</span>
        </div>

        <div className="flex gap-2 mt-2">
          <Button
            type="neutral"
            className="flex-1 rounded-xl"
            onClick={onClose}
          >
            Đóng
          </Button>
          {canEdit && (
            <Button
              className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
              onClick={() => {
                const target = item;
                onClose();
                onOpenEdit(target);
              }}
            >
              Chỉnh sửa
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};
