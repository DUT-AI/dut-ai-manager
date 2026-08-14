import React from 'react';
import { Modal, Button, Icon } from 'zmp-ui';
import {
  RequestCategory,
  CATEGORY_LABELS,
  PermissionRequestResponse,
} from '@/types/permission.types';
import type { MeetingItem } from '@/services/api/meeting.service';
import type { HomeworkItem } from '@/services/api/homework.service';

interface PermissionFormModalProps {
  isOpen: boolean;
  editingItem: PermissionRequestResponse | null;
  formCategory: RequestCategory;
  formMeetingId: number | undefined;
  formHomeworkId: number | undefined;
  formStartTime: string;
  formLateTime: string;
  formNote: string;
  meetings: MeetingItem[];
  homeworks: HomeworkItem[];
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  setFormCategory: (cat: RequestCategory) => void;
  setFormMeetingId: (id: number | undefined) => void;
  setFormHomeworkId: (id: number | undefined) => void;
  setFormStartTime: (time: string) => void;
  setFormLateTime: (time: string) => void;
  setFormNote: (note: string) => void;
  formatDate: (date?: string | null) => string;
}

export const PermissionFormModal: React.FC<PermissionFormModalProps> = ({
  isOpen,
  editingItem,
  formCategory,
  formMeetingId,
  formHomeworkId,
  formStartTime,
  formLateTime,
  formNote,
  meetings,
  homeworks,
  isSubmitting,
  onClose,
  onSubmit,
  setFormCategory,
  setFormMeetingId,
  setFormHomeworkId,
  setFormStartTime,
  setFormLateTime,
  setFormNote,
  formatDate,
}) => {
  return (
    <Modal
      visible={isOpen}
      title={editingItem ? 'Chỉnh sửa Đơn xin phép' : 'Tạo Đơn xin phép mới'}
      onClose={onClose}
      maskClosable
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-3 py-2">
        {/* Category selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-700">Loại đơn *</label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(CATEGORY_LABELS).map(([key, value]) => (
              <button
                type="button"
                key={key}
                onClick={() => setFormCategory(key as RequestCategory)}
                className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all text-left flex items-center justify-between ${
                  formCategory === key
                    ? 'bg-blue-50 border-blue-500 text-blue-700 shadow-xs'
                    : 'bg-white border-gray-200 text-gray-600'
                }`}
              >
                <span>{value.label}</span>
                {formCategory === key && <Icon icon="zi-check" size={14} />}
              </button>
            ))}
          </div>
        </div>

        {/* Meeting selector */}
        {(formCategory === RequestCategory.ABSENCE || formCategory === RequestCategory.LATE) && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Buổi sinh hoạt / Họp *</label>
            <select
              value={formMeetingId || ''}
              onChange={(e) => setFormMeetingId(Number(e.target.value))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-xs outline-none focus:border-blue-500 bg-white"
            >
              {meetings.length === 0 ? (
                <option value="">Không có buổi sinh hoạt nào sắp tới</option>
              ) : (
                meetings.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title} ({formatDate(m.start_time)})
                  </option>
                ))
              )}
            </select>
          </div>
        )}

        {/* Homework selector */}
        {formCategory === RequestCategory.POSTPONE && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Bài tập cần hoãn *</label>
            <select
              value={formHomeworkId || ''}
              onChange={(e) => setFormHomeworkId(Number(e.target.value))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-xs outline-none focus:border-blue-500 bg-white"
            >
              {homeworks.length === 0 ? (
                <option value="">Không có bài tập nào</option>
              ) : (
                homeworks.map((hw) => (
                  <option key={hw.id} value={hw.id}>
                    {hw.title} (Hạn: {formatDate(hw.deadline)})
                  </option>
                ))
              )}
            </select>
          </div>
        )}

        {/* Late time input */}
        {formCategory === RequestCategory.LATE && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Giờ dự kiến có mặt *</label>
            <input
              type="time"
              value={formLateTime}
              onChange={(e) => setFormLateTime(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 bg-white"
            />
          </div>
        )}

        {/* Postpone deadline input */}
        {formCategory === RequestCategory.POSTPONE && (
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-gray-700">Hạn nộp mới (Deadline mới) *</label>
              <span className="text-[10px] text-amber-600 font-semibold">Tối đa 4 ngày</span>
            </div>
            <input
              type="datetime-local"
              value={formStartTime}
              onChange={(e) => setFormStartTime(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 bg-white"
            />
          </div>
        )}

        {/* Note / Reason */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-700">Lý do chi tiết *</label>
          <textarea
            rows={3}
            placeholder="Nhập lý do cụ thể..."
            value={formNote}
            onChange={(e) => setFormNote(e.target.value)}
            className="w-full border border-gray-200 rounded-xl p-3 text-sm outline-none focus:border-blue-500 resize-none bg-white"
          />
        </div>

        <div className="flex gap-2 mt-3">
          <Button
            type="neutral"
            className="flex-1 rounded-xl"
            onClick={onClose}
          >
            Hủy
          </Button>
          <Button
            htmlType="submit"
            loading={isSubmitting}
            className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
          >
            {editingItem ? 'Lưu thay đổi' : 'Gửi đơn'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
