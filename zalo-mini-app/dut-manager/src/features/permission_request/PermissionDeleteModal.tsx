import React from 'react';
import { Modal, Button } from 'zmp-ui';

interface PermissionDeleteModalProps {
  deletingId: number | null;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const PermissionDeleteModal: React.FC<PermissionDeleteModalProps> = ({
  deletingId,
  isDeleting,
  onClose,
  onConfirm,
}) => {
  return (
    <Modal
      visible={deletingId !== null}
      title="Xác nhận xóa đơn"
      onClose={onClose}
    >
      <div className="flex flex-col gap-4 py-2">
        <p className="text-sm text-gray-600">
          Bạn có chắc chắn muốn xóa đơn xin phép này không? Thao tác này không thể hoàn tác.
        </p>
        <div className="flex gap-2">
          <Button
            type="neutral"
            className="flex-1 rounded-xl"
            onClick={onClose}
          >
            Hủy
          </Button>
          <Button
            type="danger"
            loading={isDeleting}
            className="flex-1 rounded-xl font-bold"
            onClick={onConfirm}
          >
            Xóa ngay
          </Button>
        </div>
      </div>
    </Modal>
  );
};
