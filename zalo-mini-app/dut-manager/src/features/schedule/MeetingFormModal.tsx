import React from 'react';
import { Modal, Button, Icon } from 'zmp-ui';
import type { MeetingResponse } from '@/types/meeting.types';
import type { UserSummary } from '@/services/api/user.service';
import type { TeamSummary } from '@/services/api/team.service';

interface MeetingFormModalProps {
  isOpen: boolean;
  editingItem: MeetingResponse | null;
  formTitle: string;
  formContent: string;
  formStartTime: string;
  formEndTime: string;
  formRequireCheckIn: boolean;
  formUserIds: number[];
  formTeamIds: number[];
  users: UserSummary[];
  teams: TeamSummary[];
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  setFormTitle: (val: string) => void;
  setFormContent: (val: string) => void;
  setFormStartTime: (val: string) => void;
  setFormEndTime: (val: string) => void;
  setFormRequireCheckIn: (val: boolean) => void;
  toggleUserId: (id: number) => void;
  toggleTeamId: (id: number) => void;
}

export const MeetingFormModal: React.FC<MeetingFormModalProps> = ({
  isOpen,
  editingItem,
  formTitle,
  formContent,
  formStartTime,
  formEndTime,
  formRequireCheckIn,
  formUserIds,
  formTeamIds,
  users,
  teams,
  isSubmitting,
  onClose,
  onSubmit,
  setFormTitle,
  setFormContent,
  setFormStartTime,
  setFormEndTime,
  setFormRequireCheckIn,
  toggleUserId,
  toggleTeamId,
}) => {
  return (
    <Modal
      visible={isOpen}
      title={editingItem ? 'Chỉnh sửa Cuộc họp' : 'Tạo Cuộc họp mới'}
      onClose={onClose}
      maskClosable
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-3 py-2">
        {/* Title */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-700">Tiêu đề cuộc họp *</label>
          <input
            type="text"
            placeholder="VD: Họp tiến độ Lab AI tuần..."
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 bg-white"
          />
        </div>

        {/* Start & End Time */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Bắt đầu *</label>
            <input
              type="datetime-local"
              value={formStartTime}
              onChange={(e) => setFormStartTime(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-2 py-2 text-xs outline-none focus:border-blue-500 bg-white"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Kết thúc *</label>
            <input
              type="datetime-local"
              value={formEndTime}
              onChange={(e) => setFormEndTime(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-2 py-2 text-xs outline-none focus:border-blue-500 bg-white"
            />
          </div>
        </div>

        {/* Check-in requirement toggle */}
        <div
          onClick={() => setFormRequireCheckIn(!formRequireCheckIn)}
          className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-200 cursor-pointer"
        >
          <div className="flex flex-col">
            <span className="text-xs font-bold text-gray-800">Yêu cầu điểm danh (Check-in)</span>
            <span className="text-[11px] text-gray-500">Chụp ảnh có mặt tại phòng họp</span>
          </div>
          <div
            className={`w-10 h-6 flex items-center rounded-full p-1 transition-all ${
              formRequireCheckIn ? 'bg-blue-600 justify-end' : 'bg-gray-300 justify-start'
            }`}
          >
            <div className="w-4 h-4 rounded-full bg-white shadow-xs"></div>
          </div>
        </div>

        {/* Teams Selector */}
        {teams.length > 0 && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">Theo Nhóm (Team)</label>
            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
              {teams.map((t) => {
                const isSelected = formTeamIds.includes(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => toggleTeamId(t.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                      isSelected
                        ? 'bg-blue-50 text-blue-700 border-blue-400'
                        : 'bg-white text-gray-600 border-gray-200'
                    }`}
                  >
                    {t.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Users Selector */}
        {users.length > 0 && (
          <div className="flex flex-col gap-1">
            <label className="text-xs font-bold text-gray-700">
              Thành viên tham gia ({formUserIds.length} đã chọn)
            </label>
            <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
              {users.map((u) => {
                const isSelected = formUserIds.includes(u.id);
                return (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => toggleUserId(u.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-600 border-gray-200'
                    }`}
                  >
                    {u.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Content / Notes */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-700">Nội dung / Ghi chú</label>
          <textarea
            rows={2}
            placeholder="Nội dung thảo luận, tài liệu chuẩn bị..."
            value={formContent}
            onChange={(e) => setFormContent(e.target.value)}
            className="w-full border border-gray-200 rounded-xl p-2.5 text-xs outline-none focus:border-blue-500 resize-none bg-white"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mt-2">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
            Hủy
          </Button>
          <Button
            htmlType="submit"
            loading={isSubmitting}
            className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
          >
            {editingItem ? 'Lưu thay đổi' : 'Tạo cuộc họp'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
