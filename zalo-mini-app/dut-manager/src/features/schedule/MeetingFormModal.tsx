import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Icon, useSnackbar } from 'zmp-ui';
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
  formEnableEvaluation: boolean;
  formUserIds: number[];
  formTeamIds: number[];
  users: UserSummary[];
  teams: TeamSummary[];
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (e?: React.FormEvent) => void;
  setFormTitle: (val: string) => void;
  setFormContent: (val: string) => void;
  setFormStartTime: (val: string) => void;
  setFormEndTime: (val: string) => void;
  setFormRequireCheckIn: (val: boolean) => void;
  setFormEnableEvaluation: (val: boolean) => void;
  toggleUserId: (id: number) => void;
  toggleTeamId: (id: number) => void;
  selectAllUsers: () => void;
  clearAllUsers: () => void;
}

export const MeetingFormModal: React.FC<MeetingFormModalProps> = ({
  isOpen,
  editingItem,
  formTitle,
  formContent,
  formStartTime,
  formEndTime,
  formRequireCheckIn,
  formEnableEvaluation,
  formUserIds = [],
  formTeamIds = [],
  users = [],
  teams = [],
  isSubmitting,
  onClose,
  onSubmit,
  setFormTitle,
  setFormContent,
  setFormStartTime,
  setFormEndTime,
  setFormRequireCheckIn,
  setFormEnableEvaluation,
  toggleUserId,
  toggleTeamId,
  selectAllUsers,
  clearAllUsers,
}) => {
  const { openSnackbar } = useSnackbar();
  const [currentStage, setCurrentStage] = useState<1 | 2>(1);
  const [searchUserQuery, setSearchUserQuery] = useState('');

  // 1. Reset stage when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setCurrentStage(1);
      setSearchUserQuery('');
    }
  }, [isOpen]);

  // Safe guarded arrays
  const safeUsers = useMemo(() => users || [], [users]);
  const safeTeams = useMemo(() => teams || [], [teams]);
  const safeUserIds = useMemo(() => formUserIds || [], [formUserIds]);
  const safeTeamIds = useMemo(() => formTeamIds || [], [formTeamIds]);

  // 2. Filter users by search input (name or email, accent-insensitive)
  // MUST ALWAYS be called unconditionally before any early return!
  const filteredUsers = useMemo(() => {
    if (!searchUserQuery.trim()) return safeUsers;
    const cleanQuery = searchUserQuery.trim().toLowerCase();
    const normQuery = cleanQuery.normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    return safeUsers.filter((u) => {
      if (!u) return false;
      const name = (u.name || '').toLowerCase();
      const email = (u.email || '').toLowerCase();
      const normName = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return (
        name.includes(cleanQuery) ||
        email.includes(cleanQuery) ||
        normName.includes(normQuery)
      );
    });
  }, [safeUsers, searchUserQuery]);

  // ALL HOOKS ARE CALLED ABOVE. SAFE TO EARLY RETURN NOW!
  if (!isOpen) return null;
  if (typeof document === 'undefined') return null;

  // Validate Stage 1 before moving to Stage 2
  const handleNextStage = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      openSnackbar({ text: 'Vui lòng nhập tiêu đề cuộc họp', type: 'warning' });
      return;
    }
    if (!formStartTime || !formEndTime) {
      openSnackbar({ text: 'Vui lòng chọn thời gian bắt đầu và kết thúc', type: 'warning' });
      return;
    }
    const startDate = new Date(formStartTime);
    const endDate = new Date(formEndTime);
    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
      openSnackbar({ text: 'Thời gian không hợp lệ', type: 'warning' });
      return;
    }
    if (startDate >= endDate) {
      openSnackbar({ text: 'Thời gian kết thúc phải sau thời gian bắt đầu', type: 'warning' });
      return;
    }
    setCurrentStage(2);
  };

  const handlePrevStage = (e: React.MouseEvent) => {
    e.preventDefault();
    setCurrentStage(1);
  };

  const handleSubmitFinal = (e: React.FormEvent) => {
    e.preventDefault();
    if (safeUserIds.length === 0) {
      openSnackbar({ text: 'Vui lòng chọn ít nhất một người hoặc nhóm tham gia!', type: 'warning' });
      return;
    }
    onSubmit(e);
  };

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-end justify-center bg-black/60 transition-opacity duration-200">
      {/* Background Mask Click to close */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Bottom Sheet Modal Container */}
      <div className="relative w-full max-w-lg bg-white rounded-t-3xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden z-10 transition-transform duration-300">
        {/* Top Handle Indicator */}
        <div className="w-full pt-3 pb-1 flex justify-center">
          <div className="w-12 h-1.5 bg-gray-200 rounded-full" />
        </div>

        {/* Header */}
        <div className="px-5 pt-1 pb-3 flex items-center justify-between border-b border-gray-100">
          <div className="flex flex-col">
            <h2 className="text-base font-bold text-gray-900 leading-snug">
              {editingItem ? 'Chỉnh sửa Buổi sinh hoạt' : 'Tạo Buổi sinh hoạt mới'}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {currentStage === 1
                ? 'Bước 1: Nhập thông tin & thiết lập'
                : `Bước 2: Phân bổ người tham gia (${safeUserIds.length} đã chọn)`}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 active:bg-gray-200 transition-colors"
          >
            <Icon icon="zi-close" size={18} />
          </button>
        </div>

        {/* Segmented Step Indicator */}
        <div className="px-5 pt-3 pb-1">
          <div className="grid grid-cols-2 p-1 bg-gray-100/90 rounded-2xl gap-1">
            <button
              type="button"
              onClick={() => setCurrentStage(1)}
              className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                currentStage === 1
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
                  currentStage === 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                1
              </span>
              <span>Thông tin chung</span>
            </button>

            <button
              type="button"
              onClick={handleNextStage}
              className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                currentStage === 2
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
                  currentStage === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                2
              </span>
              <span>Người tham gia ({safeUserIds.length})</span>
            </button>
          </div>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmitFinal} className="flex-1 overflow-y-auto px-5 py-3 flex flex-col gap-4">
          {/* ======================================================== */}
          {/* STAGE 1: THÔNG TIN CHUNG & CẤU HÌNH */}
          {/* ======================================================== */}
          {currentStage === 1 && (
            <div className="flex flex-col gap-3.5">
              {/* Tiêu đề */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-gray-700 flex items-center gap-1">
                  <span>Tiêu đề buổi sinh hoạt</span>
                  <span className="text-rose-500 font-bold">*</span>
                </label>
                <input
                  type="text"
                  placeholder="VD: Sinh hoạt định kỳ tuần 1..."
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl px-3.5 py-3 text-sm text-gray-900 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all placeholder:text-gray-400"
                />
              </div>

              {/* Thời gian Bắt đầu & Kết thúc */}
              <div className="grid grid-cols-2 gap-2.5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-gray-700 flex items-center gap-1">
                    <span>Bắt đầu</span>
                    <span className="text-rose-500 font-bold">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formStartTime}
                    onChange={(e) => setFormStartTime(e.target.value)}
                    className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl px-3 py-2.5 text-xs text-gray-800 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all font-medium"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-gray-700 flex items-center gap-1">
                    <span>Kết thúc</span>
                    <span className="text-rose-500 font-bold">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formEndTime}
                    onChange={(e) => setFormEndTime(e.target.value)}
                    className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl px-3 py-2.5 text-xs text-gray-800 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all font-medium"
                  />
                </div>
              </div>

              {/* Nội dung / Ghi chú */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-gray-700">Nội dung / Ghi chú</label>
                <textarea
                  rows={3}
                  placeholder="Mô tả chi tiết nội dung sinh hoạt, tài liệu chuẩn bị..."
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl p-3 text-xs text-gray-900 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all resize-none placeholder:text-gray-400 leading-relaxed"
                />
              </div>

              {/* Switches Container */}
              <div className="flex flex-col gap-2.5 pt-1">
                {/* Switch Điểm danh */}
                <div
                  onClick={() => setFormRequireCheckIn(!formRequireCheckIn)}
                  className={`flex items-center justify-between p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    formRequireCheckIn
                      ? 'bg-blue-50/60 border-blue-200'
                      : 'bg-gray-50/60 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        formRequireCheckIn ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      <Icon icon="zi-check-circle" size={18} />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-gray-900">Yêu cầu điểm danh (Check-in)</span>
                      <span className="text-[11px] text-gray-500">Chụp ảnh có mặt tại phòng sinh hoạt</span>
                    </div>
                  </div>

                  <div
                    className={`w-11 h-6.5 flex items-center rounded-full p-1 transition-colors shrink-0 ${
                      formRequireCheckIn ? 'bg-blue-600 justify-end' : 'bg-gray-300 justify-start'
                    }`}
                  >
                    <div className="w-4.5 h-4.5 rounded-full bg-white shadow-md" />
                  </div>
                </div>

                {/* Switch Đánh giá 2 chiều */}
                <div
                  onClick={() => setFormEnableEvaluation(!formEnableEvaluation)}
                  className={`flex items-center justify-between p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    formEnableEvaluation
                      ? 'bg-indigo-50/70 border-indigo-200'
                      : 'bg-gray-50/60 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        formEnableEvaluation ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      <Icon icon="zi-star-solid" size={18} />
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-gray-900">Đánh giá 2 chiều (24h)</span>
                        <span className="text-[9px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-bold">
                          Web
                        </span>
                      </div>
                      <span className="text-[11px] text-gray-500">
                        Trainer chấm lớp & Trainee đánh giá buổi học
                      </span>
                    </div>
                  </div>

                  <div
                    className={`w-11 h-6.5 flex items-center rounded-full p-1 transition-colors shrink-0 ${
                      formEnableEvaluation ? 'bg-indigo-600 justify-end' : 'bg-gray-300 justify-start'
                    }`}
                  >
                    <div className="w-4.5 h-4.5 rounded-full bg-white shadow-md" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* STAGE 2: THÀNH VIÊN & TEAM THAM GIA */}
          {/* ======================================================== */}
          {currentStage === 2 && (
            <div className="flex flex-col gap-3.5">
              {/* Quick Actions Bar */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-blue-50/50 border border-blue-100">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                    {safeUserIds.length}
                  </div>
                  <span className="text-xs font-bold text-gray-800">
                    Đã chọn ({safeUserIds.length}/{safeUsers.length})
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={selectAllUsers}
                    className="text-xs font-bold text-blue-600 px-2 py-1 rounded-lg hover:bg-blue-100 active:scale-95 transition-all"
                  >
                    Chọn tất cả
                  </button>
                  <span className="text-gray-300 font-light">|</span>
                  <button
                    type="button"
                    onClick={clearAllUsers}
                    className="text-xs font-bold text-rose-500 px-2 py-1 rounded-lg hover:bg-rose-100 active:scale-95 transition-all"
                  >
                    Xóa tất cả
                  </button>
                </div>
              </div>

              {/* Group By Teams (Chọn theo nhóm) */}
              {safeTeams.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-gray-700">Chọn nhanh theo Nhóm (Team)</label>
                  <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto pr-0.5">
                    {safeTeams.map((t) => {
                      const isSelected = safeTeamIds.includes(t.id);
                      const teamName = t.team_name || (t as any).name || `Nhóm #${t.id}`;
                      return (
                        <div
                          key={t.id}
                          onClick={() => toggleTeamId(t.id)}
                          className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                            isSelected
                              ? 'bg-blue-50 border-blue-500 text-blue-700'
                              : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <Icon icon="zi-members" size={16} className={isSelected ? 'text-blue-600' : 'text-gray-400'} />
                            <span className="text-xs font-bold truncate">{teamName}</span>
                          </div>
                          {isSelected && <Icon icon="zi-check" size={14} className="text-blue-600 shrink-0" />}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Search User Input */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-gray-700">Danh sách thành viên chi tiết</label>
                <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-3 py-2.5">
                  <Icon icon="zi-search" size={18} className="text-gray-400 shrink-0" />
                  <input
                    type="text"
                    placeholder="Tìm theo tên hoặc email thành viên..."
                    value={searchUserQuery}
                    onChange={(e) => setSearchUserQuery(e.target.value)}
                    className="bg-transparent border-none outline-none text-xs w-full text-gray-900 placeholder:text-gray-400"
                  />
                  {searchUserQuery && (
                    <button type="button" onClick={() => setSearchUserQuery('')} className="text-gray-400">
                      <Icon icon="zi-close-circle" size={16} />
                    </button>
                  )}
                </div>

                {/* User Cards Vertical List */}
                <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto pr-0.5 mt-1 border border-gray-100 rounded-2xl p-1 bg-gray-50/50">
                  {filteredUsers.length === 0 ? (
                    <div className="py-6 text-center text-xs text-gray-400">Không tìm thấy thành viên phù hợp</div>
                  ) : (
                    filteredUsers.map((u) => {
                      const isSelected = safeUserIds.includes(u.id);
                      return (
                        <div
                          key={u.id}
                          onClick={() => toggleUserId(u.id)}
                          className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer ${
                            isSelected
                              ? 'bg-blue-50/80 border-blue-300 text-blue-900'
                              : 'bg-white border-gray-200 text-gray-800 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div
                              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                                isSelected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {u.name ? u.name.charAt(0).toUpperCase() : 'U'}
                            </div>
                            <div className="flex flex-col min-w-0">
                              <span className="text-xs font-bold truncate leading-tight">{u.name || 'Người dùng'}</span>
                              <span className="text-[10px] text-gray-400 truncate leading-tight">{u.email}</span>
                            </div>
                          </div>

                          <div
                            className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 border transition-colors ${
                              isSelected
                                ? 'bg-blue-600 border-blue-600 text-white'
                                : 'bg-white border-gray-300'
                            }`}
                          >
                            {isSelected && <Icon icon="zi-check" size={12} />}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          )}
        </form>

        {/* Modal Sticky Bottom Actions */}
        <div className="p-4 bg-white border-t border-gray-100 flex items-center gap-2.5">
          {currentStage === 1 ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="w-1/3 py-3 rounded-2xl border border-gray-200 text-gray-600 font-bold text-xs active:bg-gray-50 transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={handleNextStage}
                className="flex-1 py-3 rounded-2xl bg-blue-600 text-white font-bold text-xs active:bg-blue-700 shadow-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Tiếp tục: Chọn người tham gia</span>
                <Icon icon="zi-chevron-right" size={14} />
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handlePrevStage}
                className="w-1/3 py-3 rounded-2xl border border-gray-200 text-gray-700 font-bold text-xs active:bg-gray-50 flex items-center justify-center gap-1 transition-colors"
              >
                <Icon icon="zi-chevron-left" size={14} />
                <span>Quay lại</span>
              </button>
              <button
                type="button"
                onClick={handleSubmitFinal}
                disabled={isSubmitting}
                className={`flex-1 py-3 rounded-2xl text-white font-bold text-xs shadow-xs flex items-center justify-center gap-1.5 transition-all active:scale-[0.99] ${
                  isSubmitting ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 active:bg-blue-700'
                }`}
              >
                {isSubmitting ? (
                  <span>Đang xử lý...</span>
                ) : (
                  <span>{editingItem ? 'Lưu thay đổi' : `Xác nhận tạo (${safeUserIds.length} người)`}</span>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default MeetingFormModal;
