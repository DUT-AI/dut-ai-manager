import React from 'react';
import { Icon } from 'zmp-ui';
import type { MeetingDetailResponse } from '@/types/meeting.types';
import { formatTime, formatDateFull } from './MeetingCard';

interface MeetingHeroCardProps {
  meeting: MeetingDetailResponse;
}

export const MeetingHeroCard: React.FC<MeetingHeroCardProps> = ({ meeting }) => {
  const start = new Date(meeting.start_time);
  const end = new Date(meeting.end_time);
  const now = new Date();
  const isOngoing = now >= start && now <= end;
  const isEnded = now > end;

  const getStatusBadge = () => {
    if (isOngoing) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          Đang diễn ra
        </span>
      );
    }
    if (isEnded) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-gray-100 text-gray-600 border border-gray-200">
          Đã kết thúc
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-600 border border-blue-200">
        Sắp diễn ra
      </span>
    );
  };

  return (
    <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h1 className="text-base font-bold text-gray-900 leading-snug">{meeting.title}</h1>
        {getStatusBadge()}
      </div>

      {meeting.content && (
        <p className="text-xs text-gray-600 leading-relaxed bg-gray-50/70 p-2.5 rounded-xl border border-gray-100">
          {meeting.content}
        </p>
      )}

      <div className="grid grid-cols-1 gap-2 pt-1 border-t border-gray-100 text-xs text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Icon icon="zi-clock-1" size={16} />
          </div>
          <div>
            <span className="font-semibold text-gray-800">
              {formatTime(meeting.start_time)} - {formatTime(meeting.end_time)}
            </span>
            <span className="text-gray-400 ml-1">({formatDateFull(meeting.start_time)})</span>
          </div>
        </div>

        {meeting.location && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
              <Icon icon="zi-location" size={16} />
            </div>
            <span className="text-gray-700 font-medium truncate">{meeting.location}</span>
          </div>
        )}

        {meeting.meeting_url && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
              <Icon icon="zi-video" size={16} />
            </div>
            <a
              href={meeting.meeting_url}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 font-medium hover:underline truncate"
            >
              Link họp trực tuyến
            </a>
          </div>
        )}

        {meeting.max_seats !== undefined && meeting.max_seats !== null && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
              <Icon icon="zi-user" size={16} />
            </div>
            <span className="text-gray-700 font-medium">
              Sức chứa tối đa: <strong className="text-indigo-600">{meeting.max_seats}</strong> chỗ
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
