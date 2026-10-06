import React from 'react';
import { Tag, Typography, Progress } from 'antd';
import {
  CheckCircleFilled,
  ClockCircleOutlined,
  CodeOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import type { ExerciseGroupSummary } from '../utils/submissionUtils';

const { Text } = Typography;

export interface ExerciseProgressOverviewProps {
  exercises: ExerciseGroupSummary[];
  selectedExerciseId: string | 'all';
  onSelectExercise: (exerciseId: string | 'all') => void;
}

export const ExerciseProgressOverview: React.FC<ExerciseProgressOverviewProps> = ({
  exercises,
  selectedExerciseId,
  onSelectExercise,
}) => {
  if (exercises.length === 0) return null;

  const totalExercises = exercises.length;
  const completedExercises = exercises.filter((e) => e.isPassed).length;
  const progressPercent = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;

  return (
    <div className="space-y-2.5 mb-4">
      {/* Header & Overall Metric */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <CodeOutlined className="text-indigo-600 text-sm" />
          <Text className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
            Tiến độ các bài tập con ({completedExercises}/{totalExercises})
          </Text>
        </div>
        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
          {progressPercent}% hoàn thành
        </span>
      </div>

      <Progress
        percent={progressPercent}
        size="small"
        strokeColor={{ '0%': '#6366f1', '100%': '#10b981' }}
        showInfo={false}
        className="!m-0"
      />

      {/* Filterable Pills / Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
        {/* 'All' Button Pill */}
        <button
          type="button"
          onClick={() => onSelectExercise('all')}
          className={`flex items-center justify-between p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
            selectedExerciseId === 'all'
              ? 'bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-400 dark:border-indigo-600 shadow-xs'
              : 'bg-white dark:bg-zinc-800/80 border-gray-200 dark:border-zinc-700/80 hover:border-indigo-200'
          }`}
        >
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-6 h-6 rounded-md bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-300 flex items-center justify-center text-xs flex-shrink-0">
              <AppstoreOutlined />
            </div>
            <div className="truncate">
              <div className="font-semibold text-xs text-gray-900 dark:text-gray-100 truncate">
                Tất cả bài nộp
              </div>
              <div className="text-[11px] text-gray-400">
                Toàn bộ lịch sử
              </div>
            </div>
          </div>
          {selectedExerciseId === 'all' && (
            <Tag color="indigo" className="m-0 text-[10px] font-medium">Đang chọn</Tag>
          )}
        </button>

        {/* Individual Exercise Summary Cards */}
        {exercises.map((ex) => {
          const isSelected = selectedExerciseId === ex.exerciseId;
          return (
            <button
              key={ex.exerciseId}
              type="button"
              onClick={() => onSelectExercise(ex.exerciseId)}
              className={`flex items-center justify-between p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? 'bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-400 dark:border-indigo-600 shadow-xs'
                  : 'bg-white dark:bg-zinc-800/80 border-gray-200 dark:border-zinc-700/80 hover:border-indigo-200'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center text-xs flex-shrink-0 ${
                  ex.isPassed
                    ? 'bg-emerald-100 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-100 dark:bg-amber-950/70 text-amber-600 dark:text-amber-400'
                }`}>
                  {ex.isPassed ? <CheckCircleFilled /> : <ClockCircleOutlined />}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-xs text-gray-900 dark:text-gray-100 truncate" title={ex.exerciseTitle}>
                    {ex.exerciseTitle}
                  </div>
                  <div className="text-[11px] text-gray-400 flex items-center gap-1.5">
                    {ex.bestScore !== null ? (
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                        {ex.bestScore}/10
                      </span>
                    ) : (
                      <span>Chưa có điểm</span>
                    )}
                    <span>• {ex.attemptCount} lần nộp</span>
                  </div>
                </div>
              </div>

              {isSelected && (
                <Tag color="indigo" className="m-0 text-[10px] font-medium flex-shrink-0">
                  Đang lọc
                </Tag>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
