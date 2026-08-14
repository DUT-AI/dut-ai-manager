import React from 'react';
import { Modal, Button } from 'zmp-ui';

interface MeetingDeleteModalProps {
  deletingId: number | null;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const MeetingDeleteModal: React.FC<MeetingDeleteModalProps> = ({
  deletingId,
  isDeleting,
  onClose,
  onConfirm,
}) => {
  return (
    <Modal visible={deletingId !== null} title="Xác nhận xóa cuộc họp" onClose={onClose}>
      <div className="flex flex-col gap-4 py-2">
        <p className="text-sm text-gray-600">
          Bạn có chắc chắn muốn xóa lịch họp này không? Dữ liệu điểm danh của cuộc họp cũng sẽ bị xóa.
        </p>
        <div className="flex gap-2">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
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
