import React from 'react';
import { Calendar } from 'zmp-ui';
import type { MeetingResponse } from '@/types/meeting.types';

interface ZaloMobileCalendarProps {
  selectedDate: Date;
  meetings: MeetingResponse[];
  onSelectDate: (date: Date) => void;
}

export const ZaloMobileCalendar: React.FC<ZaloMobileCalendarProps> = ({
  selectedDate,
  meetings,
  onSelectDate,
}) => {
  // Map meetings by date (YYYY-MM-DD)
  const meetingDateCounts = React.useMemo(() => {
    const map: Record<string, number> = {};
    meetings.forEach((m) => {
      const dStr = m.start_time.slice(0, 10);
      map[dStr] = (map[dStr] || 0) + 1;
    });
    return map;
  }, [meetings]);

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-3 overflow-hidden">
      <Calendar
        value={selectedDate}
        onSelect={(date) => {
          if (date) {
            onSelectDate(date);
          }
        }}
        cellRender={(date) => {
          const toISO = (d: Date) => {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
          };

          const dStr = toISO(date);
          const count = meetingDateCounts[dStr] || 0;

          if (count > 0) {
            return (
              <div className="flex flex-col items-center justify-center -mt-1">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              </div>
            );
          }
          return null;
        }}
      />
    </div>
  );
};
