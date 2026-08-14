import React from 'react';
import { Button, Icon } from 'zmp-ui';

interface PermissionHeaderProps {
  total: number;
  onOpenCreate: () => void;
}

export const PermissionHeader: React.FC<PermissionHeaderProps> = ({
  total,
  onOpenCreate,
}) => {
  return (
    <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center justify-between">
      <div className="flex flex-col">
        <span className="font-bold text-gray-900 text-base">Danh sách đơn</span>
        <span className="text-xs text-gray-500">
          Tổng cộng: <strong className="text-blue-600 font-semibold">{total}</strong> đơn
        </span>
      </div>

      <Button
        size="small"
        className="rounded-xl flex items-center gap-1 font-bold text-xs bg-blue-600 text-white shadow-xs"
        onClick={onOpenCreate}
      >
        <Icon icon="zi-plus" size={16} />
        <span>Tạo đơn mới</span>
      </Button>
    </div>
  );
};
