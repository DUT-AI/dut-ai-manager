import React from 'react';
import { Icon, Button } from 'zmp-ui';
import {
  PermissionRequestResponse,
  RequestCategory,
  CATEGORY_LABELS,
} from '@/types/permission.types';

interface PermissionCardProps {
  item: PermissionRequestResponse;
  currentUserId?: number;
  hasDeletePermission: boolean;
  hasUpdatePermission: boolean;
  onViewDetail: (item: PermissionRequestResponse) => void;
  onEdit: (item: PermissionRequestResponse) => void;
  onDelete: (id: number) => void;
}

export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return 'Chưa xác định';
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

export const PermissionCard: React.FC<PermissionCardProps> = ({
  item,
  currentUserId,
  hasDeletePermission,
  hasUpdatePermission,
  onViewDetail,
  onEdit,
  onDelete,
}) => {
  const catInfo =
    CATEGORY_LABELS[item.category as RequestCategory] || {
      label: item.category,
      color: 'text-gray-700',
      bg: 'bg-gray-100 border-gray-200',
    };

  const isOwner = currentUserId && item.owner?.id === currentUserId;
  const canUpdate = isOwner || hasUpdatePermission;
  const canDelete = isOwner || hasDeletePermission;

  const relatedTitle =
    item.category === RequestCategory.POSTPONE
      ? item.homework?.title || (item.homework_id ? `Bài tập #${item.homework_id}` : null)
      : item.meeting?.title || (item.meeting_id ? `Buổi họp #${item.meeting_id}` : null);

  return (
    <div
      onClick={() => onViewDetail(item)}
      className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col gap-3 active:scale-[0.99] transition-transform cursor-pointer"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${catInfo.bg} ${catInfo.color}`}
          >
            {catInfo.label}
          </span>
          {item.owner?.name && (
            <span className="text-xs font-semibold text-gray-800">
              {item.owner.name}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {canUpdate && (
            <button
              onClick={() => onEdit(item)}
              className="text-gray-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <Icon icon="zi-edit-text" size={16} />
            </button>
          )}
          {canDelete && (
            <button
              onClick={() => onDelete(item.id)}
              className="text-gray-400 hover:text-rose-500 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <Icon icon="zi-delete" size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Related Meeting or Homework Badge */}
      {relatedTitle && (
        <div className="flex items-center gap-1.5 text-xs text-blue-700 bg-blue-50/70 px-2.5 py-1 rounded-lg w-fit">
          <Icon icon="zi-info-circle" size={14} />
          <span className="font-semibold">{relatedTitle}</span>
        </div>
      )}

      {/* Note / Reason */}
      <p className="text-sm text-gray-700 leading-relaxed font-medium bg-gray-50/80 p-3 rounded-xl">
        {item.note}
      </p>

      {/* Meta Info */}
      <div className="flex items-center justify-between text-[11px] text-gray-400 pt-1 border-t border-gray-50">
        <div className="flex items-center gap-1">
          <Icon icon="zi-clock-1" size={13} />
          <span>
            {item.category === 'LATE'
              ? `Có mặt lúc: ${formatDate(item.start_time)}`
              : item.category === 'POSTPONE'
              ? `Hạn mới: ${formatDate(item.start_time)}`
              : formatDate(item.created_at)}
          </span>
        </div>
        <span>{formatDate(item.created_at)}</span>
      </div>
    </div>
  );
};

interface PermissionListProps {
  permissions: PermissionRequestResponse[];
  isLoading: boolean;
  currentUserId?: number;
  hasDeletePermission: boolean;
  hasUpdatePermission: boolean;
  onOpenCreate: () => void;
  onViewDetail: (item: PermissionRequestResponse) => void;
  onEdit: (item: PermissionRequestResponse) => void;
  onDelete: (id: number) => void;
}

export const PermissionList: React.FC<PermissionListProps> = ({
  permissions,
  isLoading,
  currentUserId,
  hasDeletePermission,
  hasUpdatePermission,
  onOpenCreate,
  onViewDetail,
  onEdit,
  onDelete,
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white p-4 rounded-2xl border border-gray-100 animate-pulse flex flex-col gap-2"
          >
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (permissions.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-gray-100 text-center flex flex-col items-center gap-3">
        <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center">
          <Icon icon="zi-note" size={28} />
        </div>
        <div className="flex flex-col gap-1">
          <p className="font-bold text-sm text-gray-800">Không có đơn xin phép nào</p>
          <p className="text-xs text-gray-400">
            Bấm "Tạo đơn mới" để xin vắng, đi trễ hoặc hoãn bài tập
          </p>
        </div>
        <Button
          size="small"
          variant="secondary"
          className="rounded-xl mt-1 font-semibold"
          onClick={onOpenCreate}
        >
          Gửi đơn ngay
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {permissions.map((item) => (
        <PermissionCard
          key={item.id}
          item={item}
          currentUserId={currentUserId}
          hasDeletePermission={hasDeletePermission}
          hasUpdatePermission={hasUpdatePermission}
          onViewDetail={onViewDetail}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
