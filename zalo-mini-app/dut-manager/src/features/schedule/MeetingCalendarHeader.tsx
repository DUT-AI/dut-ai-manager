import React from 'react';
import { Button, Icon } from 'zmp-ui';

interface MeetingCalendarHeaderProps {
  currentWeekLabel: string;
  totalMeetings: number;
  isCurrentWeek: boolean;
  canCreate: boolean;
  onPrevWeek: () => void;
  onNextWeek: () => void;
  onToday: () => void;
  onOpenCreate: () => void;
}

export const MeetingCalendarHeader: React.FC<MeetingCalendarHeaderProps> = ({
  currentWeekLabel,
  totalMeetings,
  isCurrentWeek,
  canCreate,
  onPrevWeek,
  onNextWeek,
  onToday,
  onOpenCreate,
}) => {
  return (
    <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-base text-gray-900">Lịch Họp & Sinh hoạt Lab</h2>
          <p className="text-xs text-gray-500">
            {currentWeekLabel} •{' '}
            <strong className="text-blue-600 font-semibold">{totalMeetings}</strong> cuộc họp
          </p>
        </div>

        {canCreate && (
          <Button
            size="small"
            className="rounded-xl flex items-center gap-1 font-bold text-xs bg-blue-600 text-white shadow-xs"
            onClick={onOpenCreate}
          >
            <Icon icon="zi-plus" size={16} />
            <span>Tạo lịch</span>
          </Button>
        )}
      </div>

      {/* Week Navigator Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <button
          onClick={onPrevWeek}
          className="p-1.5 rounded-lg border border-gray-200 text-gray-600 active:bg-gray-100"
        >
          <Icon icon="zi-chevron-left" size={18} />
        </button>

        <button
          onClick={onToday}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            isCurrentWeek
              ? 'bg-blue-600 text-white shadow-xs'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Tuần này
        </button>

        <button
          onClick={onNextWeek}
          className="p-1.5 rounded-lg border border-gray-200 text-gray-600 active:bg-gray-100"
        >
          <Icon icon="zi-chevron-right" size={18} />
        </button>
      </div>
    </div>
  );
};
