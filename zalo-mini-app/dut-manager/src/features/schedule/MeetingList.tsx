import React from 'react';
import { Icon, Button } from 'zmp-ui';
import type { MeetingResponse } from '@/types/meeting.types';
import { MeetingCard, formatDateFull } from './MeetingCard';

interface MeetingListProps {
  meetings: MeetingResponse[];
  isLoading: boolean;
  currentUserId?: number;
  hasUpdatePermission: boolean;
  hasDeletePermission: boolean;
  canCreate: boolean;
  onOpenCreate: () => void;
  onSelectMeeting: (meeting: MeetingResponse) => void;
  onEditMeeting: (meeting: MeetingResponse) => void;
  onDeleteMeeting: (id: number) => void;
}

export const MeetingList: React.FC<MeetingListProps> = ({
  meetings,
  isLoading,
  currentUserId,
  hasUpdatePermission,
  hasDeletePermission,
  canCreate,
  onOpenCreate,
  onSelectMeeting,
  onEditMeeting,
  onDeleteMeeting,
}) => {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white p-4 rounded-2xl border border-gray-100 animate-pulse flex flex-col gap-2"
          >
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (meetings.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-gray-100 text-center flex flex-col items-center gap-3">
        <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center">
          <Icon icon="zi-calendar" size={28} />
        </div>
        <div className="flex flex-col gap-1">
          <p className="font-bold text-sm text-gray-800">Không có lịch họp nào trong tuần</p>
          <p className="text-xs text-gray-400">
            Hãy chọn tuần khác hoặc bấm tạo lịch họp mới
          </p>
        </div>
        {canCreate && (
          <Button
            size="small"
            variant="secondary"
            className="rounded-xl mt-1 font-semibold"
            onClick={onOpenCreate}
          >
            Tạo cuộc họp mới
          </Button>
        )}
      </div>
    );
  }

  // Group meetings by Date
  const groupedMeetings: { [dateStr: string]: MeetingResponse[] } = {};
  meetings.forEach((m) => {
    const dKey = m.start_time.slice(0, 10);
    if (!groupedMeetings[dKey]) {
      groupedMeetings[dKey] = [];
    }
    groupedMeetings[dKey].push(m);
  });

  return (
    <div className="flex flex-col gap-5">
      {Object.entries(groupedMeetings).map(([dateStr, dayMeetings]) => (
        <div key={dateStr} className="flex flex-col gap-2.5">
          {/* Day Label Header */}
          <div className="flex items-center gap-2 px-1">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <span className="font-bold text-xs text-gray-700 uppercase tracking-wide">
              {formatDateFull(dayMeetings[0].start_time)}
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {dayMeetings.map((meeting) => (
              <MeetingCard
                key={meeting.id}
                meeting={meeting}
                currentUserId={currentUserId}
                hasUpdatePermission={hasUpdatePermission}
                hasDeletePermission={hasDeletePermission}
                onClick={() => onSelectMeeting(meeting)}
                onEdit={onEditMeeting}
                onDelete={onDeleteMeeting}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
