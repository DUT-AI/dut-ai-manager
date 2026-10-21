import React from 'react';
import type { ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';

interface MeetingStatsCardProps {
  participants: ParticipantResponse[];
}

export const MeetingStatsCard: React.FC<MeetingStatsCardProps> = ({ participants }) => {
  const total = participants.length;

  const joinedCount = participants.filter(
    (p) => p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED
  ).length;

  const absentCount = participants.filter(
    (p) =>
      p.status === ParticipantStatus.ABSENT_EXCUSED ||
      p.status === ParticipantStatus.ABSENT_UNEXCUSED
  ).length;

  const lateCount = participants.filter(
    (p) =>
      p.status === ParticipantStatus.LATE_EXCUSED ||
      p.status === ParticipantStatus.LATE_UNEXCUSED
  ).length;

  const notJoinedCount = participants.filter(
    (p) => p.status === ParticipantStatus.NOT_JOINED
  ).length;

  return (
    <div className="bg-white rounded-2xl p-3.5 border border-gray-100 shadow-sm flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-gray-800">Thống kê sĩ số</span>
        <span className="text-xs text-gray-500 font-medium">
          Tổng danh sách: <strong className="text-gray-900">{total}</strong>
        </span>
      </div>

      <div className="grid grid-cols-4 gap-2 pt-1">
        <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-emerald-50/70 border border-emerald-100">
          <span className="text-base font-extrabold text-emerald-600">{joinedCount}</span>
          <span className="text-[10px] font-semibold text-emerald-800 mt-0.5">Có mặt</span>
        </div>

        <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-orange-50/70 border border-orange-100">
          <span className="text-base font-extrabold text-orange-600">{lateCount}</span>
          <span className="text-[10px] font-semibold text-orange-800 mt-0.5">Đi trễ</span>
        </div>

        <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-rose-50/70 border border-rose-100">
          <span className="text-base font-extrabold text-rose-600">{absentCount}</span>
          <span className="text-[10px] font-semibold text-rose-800 mt-0.5">Vắng</span>
        </div>

        <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-gray-50 border border-gray-200/70">
          <span className="text-base font-extrabold text-gray-600">{notJoinedCount}</span>
          <span className="text-[10px] font-semibold text-gray-700 mt-0.5">Chưa vào</span>
        </div>
      </div>
    </div>
  );
};
