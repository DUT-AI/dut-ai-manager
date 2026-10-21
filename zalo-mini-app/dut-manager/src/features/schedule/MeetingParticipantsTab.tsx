import React, { useRef, useState } from 'react';
import { Button, Icon, useSnackbar, Avatar } from 'zmp-ui';
import type { ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';
import { meetingService } from '@/services/api/meeting.service';
import { formatTime } from './MeetingCard';

interface MeetingParticipantsTabProps {
  meetingId: number;
  participants: ParticipantResponse[];
  currentUserId?: number;
  hasUpdatePermission: boolean;
  onEditParticipantStatus?: (participant: ParticipantResponse) => void;
  onRefetch: () => void;
}

export const MeetingParticipantsTab: React.FC<MeetingParticipantsTabProps> = ({
  meetingId,
  participants,
  currentUserId,
  hasUpdatePermission,
  onEditParticipantStatus,
  onRefetch,
}) => {
  const { openSnackbar } = useSnackbar();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isCheckingIn, setIsCheckingIn] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const myParticipant = participants.find((p) => p.user_id === currentUserId);
  const myCheckedIn =
    myParticipant?.status === ParticipantStatus.JOINED ||
    myParticipant?.status === ParticipantStatus.COMPLETED;

  const handleTriggerCheckIn = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentUserId) return;

    setIsCheckingIn(true);
    try {
      const res = await meetingService.checkIn(meetingId, currentUserId, file);
      if (res.is_success) {
        openSnackbar({ text: 'Điểm danh thành công!', type: 'success' });
        onRefetch();
      } else {
        openSnackbar({ text: res.message || 'Điểm danh thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Lỗi khi gửi ảnh điểm danh', type: 'error' });
    } finally {
      setIsCheckingIn(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getStatusBadge = (status: ParticipantStatus) => {
    switch (status) {
      case ParticipantStatus.JOINED:
      case ParticipantStatus.COMPLETED:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Có mặt
          </span>
        );
      case ParticipantStatus.LATE_EXCUSED:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-50 text-orange-700 border border-orange-200">
            Trễ có phép
          </span>
        );
      case ParticipantStatus.LATE_UNEXCUSED:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
            Trễ không phép
          </span>
        );
      case ParticipantStatus.ABSENT_EXCUSED:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
            Vắng có phép
          </span>
        );
      case ParticipantStatus.ABSENT_UNEXCUSED:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-800 border border-red-200">
            Vắng không phép
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-600 border border-gray-200">
            Chưa vào
          </span>
        );
    }
  };

  const filteredParticipants = participants.filter((p) => {
    if (filterStatus === 'ALL') return true;
    if (filterStatus === 'JOINED')
      return p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED;
    if (filterStatus === 'ABSENT')
      return (
        p.status === ParticipantStatus.ABSENT_EXCUSED ||
        p.status === ParticipantStatus.ABSENT_UNEXCUSED
      );
    if (filterStatus === 'LATE')
      return (
        p.status === ParticipantStatus.LATE_EXCUSED ||
        p.status === ParticipantStatus.LATE_UNEXCUSED
      );
    return true;
  });

  return (
    <div className="flex flex-col gap-3">
      {/* Check-in Banner for current user */}
      {myParticipant && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold">
              <Icon icon="zi-camera" size={20} />
            </div>
            <div>
              <p className="text-xs font-bold text-gray-900">Điểm danh cá nhân</p>
              <p className="text-[11px] text-gray-500">
                {myCheckedIn
                  ? `Đã điểm danh lúc ${myParticipant.check_in_at ? formatTime(myParticipant.check_in_at) : ''}`
                  : 'Chưa điểm danh buổi học này'}
              </p>
            </div>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />

          {!myCheckedIn ? (
            <Button
              size="small"
              loading={isCheckingIn}
              onClick={handleTriggerCheckIn}
              className="rounded-xl font-bold bg-blue-600 text-white text-xs px-3 shadow-xs"
            >
              Chụp ảnh
            </Button>
          ) : (
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
              <Icon icon="zi-check-circle-solid" size={16} /> Đã vào
            </span>
          )}
        </div>
      )}

      {/* Filter Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {[
          { key: 'ALL', label: `Tất cả (${participants.length})` },
          {
            key: 'JOINED',
            label: `Có mặt (${
              participants.filter(
                (p) =>
                  p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED
              ).length
            })`,
          },
          {
            key: 'LATE',
            label: `Trễ (${
              participants.filter(
                (p) =>
                  p.status === ParticipantStatus.LATE_EXCUSED ||
                  p.status === ParticipantStatus.LATE_UNEXCUSED
              ).length
            })`,
          },
          {
            key: 'ABSENT',
            label: `Vắng (${
              participants.filter(
                (p) =>
                  p.status === ParticipantStatus.ABSENT_EXCUSED ||
                  p.status === ParticipantStatus.ABSENT_UNEXCUSED
              ).length
            })`,
          },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterStatus(tab.key)}
            className={`px-3 py-1.5 rounded-xl font-medium shrink-0 transition-all ${
              filterStatus === tab.key
                ? 'bg-blue-600 text-white shadow-xs font-bold'
                : 'bg-white border border-gray-200 text-gray-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Participants List */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-100 overflow-hidden">
        {filteredParticipants.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-400">
            Không có thành viên nào trong danh sách
          </div>
        ) : (
          filteredParticipants.map((p) => {
            const isMe = p.user_id === currentUserId;
            return (
              <div
                key={p.id}
                className="p-3 flex items-center justify-between gap-3 hover:bg-gray-50/60 transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Avatar
                    src={p.user_avatar_url || undefined}
                    size={36}
                    className="shrink-0 bg-blue-100 text-blue-600 font-bold"
                  >
                    {p.user_name?.charAt(0)?.toUpperCase() || 'U'}
                  </Avatar>
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-gray-900 truncate">
                        {p.user_name || `Thành viên #${p.user_id}`}
                      </span>
                      {isMe && (
                        <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.2 rounded-md">
                          Bạn
                        </span>
                      )}
                    </div>
                    {p.check_in_at && (
                      <span className="text-[10px] text-gray-400">
                        Check-in: {formatTime(p.check_in_at)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {getStatusBadge(p.status)}

                  {hasUpdatePermission && onEditParticipantStatus && (
                    <button
                      onClick={() => onEditParticipantStatus(p)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                      title="Chỉnh sửa trạng thái"
                    >
                      <Icon icon="zi-edit-text" size={16} />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
