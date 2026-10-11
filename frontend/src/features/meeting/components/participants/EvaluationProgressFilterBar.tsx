import React from 'react';
import { Card, Progress, Segmented, Typography } from 'antd';

const { Text } = Typography;

interface Props {
  totalParticipants: number;
  totalActiveTrainees: number;
  trainerEvaluatedCount: number;
  traineeEvaluatedCount: number;
  unratedCount: number;
  evalFilter: 'all' | 'unrated' | 'rated';
  onFilterChange: (val: 'all' | 'unrated' | 'rated') => void;
}

export const EvaluationProgressFilterBar: React.FC<Props> = ({
  totalParticipants,
  totalActiveTrainees,
  trainerEvaluatedCount,
  traineeEvaluatedCount,
  unratedCount,
  evalFilter,
  onFilterChange,
}) => {
  const trainerEvalPercent =
    totalActiveTrainees > 0
      ? Math.round((trainerEvaluatedCount / totalActiveTrainees) * 100)
      : 0;
  const traineeEvalPercent =
    totalActiveTrainees > 0
      ? Math.round((traineeEvaluatedCount / totalActiveTrainees) * 100)
      : 0;

  return (
    <Card size="small" className="bg-gray-50/80 border-gray-200/80 shadow-none rounded-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Progress Bars */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-6 flex-1">
          <div className="flex-1">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-medium text-gray-700">
                👨‍🏫 Trainer đánh giá Học viên:
              </span>
              <span className="font-semibold text-emerald-700">
                {trainerEvaluatedCount} / {totalActiveTrainees} ({trainerEvalPercent}%)
              </span>
            </div>
            <Progress
              percent={trainerEvalPercent}
              size="small"
              strokeColor="#10b981"
              showInfo={false}
            />
          </div>

          <div className="flex-1">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-medium text-gray-700">
                🎓 Học viên đánh giá Trainer:
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
        </div>

        {/* Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-gray-200/60">
          <Text type="secondary" className="text-xs">
            Lọc theo trạng thái chấm:
          </Text>
          <div className="overflow-x-auto no-scrollbar -mx-1 px-1">
            <Segmented
              size="small"
              value={evalFilter}
              onChange={(val) => onFilterChange(val as any)}
              className="text-xs"
              options={[
                { label: `Tất cả (${totalParticipants})`, value: 'all' },
                { label: `Chưa chấm (${unratedCount})`, value: 'unrated' },
                { label: `Đã chấm (${trainerEvaluatedCount})`, value: 'rated' },
              ]}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};
