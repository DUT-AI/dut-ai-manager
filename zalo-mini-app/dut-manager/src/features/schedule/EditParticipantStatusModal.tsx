import React, { useState } from 'react';
import { Modal, Button, Icon, useSnackbar } from 'zmp-ui';
import type { ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';
import { meetingService } from '@/services/api/meeting.service';

interface EditParticipantStatusModalProps {
  meetingId: number;
  participant: ParticipantResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const EditParticipantStatusModal: React.FC<EditParticipantStatusModalProps> = ({
  meetingId,
  participant,
  onClose,
  onSuccess,
}) => {
  const { openSnackbar } = useSnackbar();
  const [selectedStatus, setSelectedStatus] = useState<ParticipantStatus>(
    participant?.status || ParticipantStatus.NOT_JOINED
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!participant) return null;

  const statusOptions = [
    { value: ParticipantStatus.JOINED, label: 'Có mặt / Đã tham gia' },
    { value: ParticipantStatus.LATE_EXCUSED, label: 'Đi trễ có phép' },
    { value: ParticipantStatus.LATE_UNEXCUSED, label: 'Đi trễ không phép' },
    { value: ParticipantStatus.ABSENT_EXCUSED, label: 'Vắng có phép' },
    { value: ParticipantStatus.ABSENT_UNEXCUSED, label: 'Vắng không phép' },
    { value: ParticipantStatus.NOT_JOINED, label: 'Chưa vào / Chưa điểm danh' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await meetingService.updateParticipantStatus(
        meetingId,
        participant.user_id,
        { status: selectedStatus }
      );
      if (res.is_success) {
        openSnackbar({ text: 'Cập nhật trạng thái thành công', type: 'success' });
        onSuccess();
        onClose();
      } else {
        openSnackbar({ text: res.message || 'Cập nhật thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Lỗi khi cập nhật trạng thái', type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      visible={!!participant}
      title="Cập nhật trạng thái điểm danh"
      onClose={onClose}
      maskClosable
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 py-2">
        <p className="text-xs text-gray-500">
          Thành viên: <strong className="text-gray-900">{participant.user_name || `#${participant.user_id}`}</strong>
        </p>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-gray-700">Trạng thái mới</label>
          <div className="flex flex-col gap-1.5">
            {statusOptions.map((opt) => (
              <button
                type="button"
                key={opt.value}
                onClick={() => setSelectedStatus(opt.value)}
                className={`p-2.5 rounded-xl text-xs font-semibold border transition-all text-left flex items-center justify-between ${
                  selectedStatus === opt.value
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'bg-white border-gray-200 text-gray-600'
                }`}
              >
                <span>{opt.label}</span>
                {selectedStatus === opt.value && <Icon icon="zi-check" size={16} />}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-2 mt-3">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
            Hủy
          </Button>
          <Button
            htmlType="submit"
            loading={isSubmitting}
            className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
          >
            Lưu thay đổi
          </Button>
        </div>
      </form>
    </Modal>
  );
};
