import React from 'react';
import { Card, Progress, Segmented, Typography } from 'antd';

const { Text } = Typography;

interface Props {
  totalParticipants: number;
  totalActiveTrainees: number;
  traineeEvaluatedCount: number;
  unratedCount: number;
  evalFilter: 'all' | 'unrated' | 'rated';
  onFilterChange: (val: 'all' | 'unrated' | 'rated') => void;
}

export const EvaluationProgressFilterBar: React.FC<Props> = ({
  totalParticipants,
  totalActiveTrainees,
  traineeEvaluatedCount,
  unratedCount,
  evalFilter,
  onFilterChange,
}) => {
  const traineeEvalPercent =
    totalActiveTrainees > 0
      ? Math.round((traineeEvaluatedCount / totalActiveTrainees) * 100)
      : 0;

  return (
    <Card size="small" className="bg-gray-50/80 border-gray-200/80 shadow-none rounded-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Progress Bar */}
        <div className="flex-1 max-w-xl">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-medium text-gray-700">
              Tiến độ Học viên đánh giá Giảng viên:
            </span>
            <span className="font-semibold text-blue-700">
              {traineeEvaluatedCount} / {totalActiveTrainees} ({traineeEvalPercent}%)
            </span>
          </div>
          <Progress
            percent={traineeEvalPercent}
            size="small"
            strokeColor="#3b82f6"
            showInfo={false}
          />
        </div>

        {/* Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-gray-200/60">
          <Text type="secondary" className="text-xs">
            Lọc theo trạng thái đánh giá:
          </Text>
          <div className="overflow-x-auto no-scrollbar -mx-1 px-1">
            <Segmented
              size="small"
              value={evalFilter}
              onChange={(val) => onFilterChange(val as any)}
              className="text-xs"
              options={[
                { label: `Tất cả (${totalParticipants})`, value: 'all' },
                { label: `Chưa đánh giá (${unratedCount})`, value: 'unrated' },
                { label: `Đã đánh giá (${traineeEvaluatedCount})`, value: 'rated' },
              ]}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};
