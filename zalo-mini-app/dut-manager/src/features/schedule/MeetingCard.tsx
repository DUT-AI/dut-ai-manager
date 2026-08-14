import React from 'react';
import { Icon } from 'zmp-ui';
import type { MeetingResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';

export const formatTime = (dateStr: string): string => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return dateStr;
  }
};

export const formatDateFull = (dateStr: string): string => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('vi-VN', {
      weekday: 'long',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

interface MeetingCardProps {
  meeting: MeetingResponse;
  currentUserId?: number;
  hasUpdatePermission: boolean;
  hasDeletePermission: boolean;
  onClick: () => void;
  onEdit: (meeting: MeetingResponse) => void;
  onDelete: (id: number) => void;
}

export const MeetingCard: React.FC<MeetingCardProps> = ({
  meeting,
  currentUserId,
  hasUpdatePermission,
  hasDeletePermission,
  onClick,
  onEdit,
  onDelete,
}) => {
  const now = new Date();
  const start = new Date(meeting.start_time);
  const end = new Date(meeting.end_time);

  const isOngoing = now >= start && now <= end;
  const isEnded = now > end;

  const totalParticipants = meeting.participants?.length || 0;
  const checkedInCount =
    meeting.participants?.filter(
      (p) => p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED
    ).length || 0;

  const myParticipant = meeting.participants?.find((p) => p.user_id === currentUserId);
  const myCheckedIn =
    myParticipant?.status === ParticipantStatus.JOINED ||
    myParticipant?.status === ParticipantStatus.COMPLETED;

  return (
    <div
      onClick={onClick}
      className={`bg-white p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-3 shadow-sm active:scale-[0.99] ${
        isOngoing
          ? 'border-emerald-300 ring-2 ring-emerald-50'
          : 'border-gray-100 hover:border-blue-200'
      }`}
    >
      {/* Top row: Status tag + Action icons */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-1.5">
          <span
            className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold border ${
              isOngoing
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 animate-pulse'
                : isEnded
                ? 'bg-gray-100 text-gray-500 border-gray-200'
                : 'bg-blue-50 text-blue-700 border-blue-200'
            }`}
          >
            {isOngoing ? '🟢 Đang diễn ra' : isEnded ? '⚫ Đã kết thúc' : '🔵 Sắp diễn ra'}
          </span>

          {meeting.require_check_in && (
            <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full font-semibold">
              Cần điểm danh
            </span>
          )}
        </div>

        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {hasUpdatePermission && (
            <button
              onClick={() => onEdit(meeting)}
              className="text-gray-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <Icon icon="zi-edit-text" size={16} />
            </button>
          )}
          {hasDeletePermission && (
            <button
              onClick={() => onDelete(meeting.id)}
              className="text-gray-400 hover:text-rose-500 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <Icon icon="zi-delete" size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Meeting Title & Content */}
      <div className="flex flex-col gap-1">
        <h3 className="font-bold text-gray-900 text-sm leading-snug">{meeting.title}</h3>
        {meeting.content && (
          <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
            {meeting.content}
          </p>
        )}
      </div>

      {/* Time & Attendance */}
      <div className="flex items-center justify-between text-xs text-gray-600 pt-2 border-t border-gray-50">
        <div className="flex items-center gap-1 font-semibold text-blue-700">
          <Icon icon="zi-clock-1" size={14} />
          <span>
            {formatTime(meeting.start_time)} - {formatTime(meeting.end_time)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {currentUserId && (
            <span
              className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ${
                myCheckedIn
                  ? 'bg-emerald-50 text-emerald-600'
                  : 'bg-gray-50 text-gray-400'
              }`}
            >
              {myCheckedIn ? '✓ Bạn đã checkin' : 'Chưa checkin'}
            </span>
          )}
          <span className="text-[11px] text-gray-400 font-medium">
            👥 {checkedInCount}/{totalParticipants}
          </span>
        </div>
      </div>
    </div>
  );
};
