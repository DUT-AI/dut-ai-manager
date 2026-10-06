import React from 'react';
import { Progress, Tag, Typography, Tooltip } from 'antd';
import {
  CodeOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import type { ExerciseSummary } from '../types/homework.types';

const { Text } = Typography;

export interface ExerciseCompletionStatsProps {
  exercises?: ExerciseSummary[] | null;
  hasGame?: boolean;
  gameSubmittedCount?: number;
  gameTotalCount?: number;
  totalAssigned?: number;
}

export const ExerciseCompletionStats: React.FC<ExerciseCompletionStatsProps> = ({
  exercises = [],
  hasGame = false,
  gameSubmittedCount = 0,
  gameTotalCount = 0,
  totalAssigned = 0,
}) => {
  const codingExercises = exercises ?? [];
  const hasMultipleCoding = codingExercises.length > 0;
  const showGameStats = hasGame && totalAssigned > 0;

  if (!hasMultipleCoding && !showGameStats) {
    return null;
  }

  const gameRate =
    totalAssigned > 0
      ? Math.round((gameSubmittedCount / totalAssigned) * 1000) / 10
      : 0;

  return (
    <div className="mb-4 p-4 rounded-2xl bg-white dark:bg-zinc-800/90 border border-gray-100 dark:border-zinc-700/80 shadow-xs">
      {/* Section Header */}
      <div className="flex items-center justify-between gap-2 mb-3 pb-2.5 border-b border-gray-100 dark:border-zinc-700/60">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-sm">
            <AppstoreOutlined />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-800 dark:text-gray-200">
              Tỉ lệ hoàn thành từng bài tập con
            </span>
            <Text type="secondary" className="block text-[11px]">
              Theo dõi chi tiết tiến độ của học viên trên từng bài coding & quiz game
            </Text>
          </div>
        </div>

        <Tag color="blue" className="m-0 text-xs font-semibold rounded-full px-2.5">
          {codingExercises.length + (hasGame ? 1 : 0)} phần bài tập
        </Tag>
      </div>

      {/* Grid of Sub-Exercise Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {/* Coding Exercises */}
        {codingExercises.map((ex, idx) => {
          const completed = ex.completed_count ?? 0;
          const assigned = ex.total_assigned || totalAssigned || 0;
          const rate =
            ex.completion_rate ??
            (assigned > 0 ? Math.round((completed / assigned) * 1000) / 10 : 0);
          const remaining = Math.max(0, assigned - completed);

          return (
            <div
              key={ex.exercise_id || ex.id || idx}
              className="flex flex-col justify-between p-3 rounded-xl bg-gray-50/70 dark:bg-zinc-900/60 border border-gray-100 dark:border-zinc-800 hover:border-indigo-200 dark:hover:border-zinc-700 transition-all shadow-2xs"
            >
              {/* Card Header */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <Tag
                    icon={<CodeOutlined />}
                    color="blue"
                    className="m-0 text-[11px] font-semibold rounded-md"
                  >
                    Bài {ex.order_index ?? idx + 1}
                  </Tag>

                  <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {rate}%
                  </span>
                </div>

                <Tooltip title={ex.title}>
                  <div className="font-semibold text-xs text-gray-800 dark:text-gray-100 line-clamp-2 min-h-[32px] leading-snug">
                    {ex.title}
                  </div>
                </Tooltip>
              </div>

              {/* Progress & Stat Details */}
              <div className="pt-2 mt-2 border-t border-gray-100 dark:border-zinc-800/80">
                <Progress
                  percent={rate}
                  showInfo={false}
                  strokeColor={{
                    '0%': '#6366f1',
                    '100%': '#10b981',
                  }}
                  trailColor="#e2e8f0"
                  size={['100%', 6]}
                  className="!m-0 mb-2"
                />

                <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                    <CheckCircleOutlined className="text-[10px]" />
                    <b>{completed}</b>/{assigned} xong
                  </span>
                  <span className="flex items-center gap-1 text-gray-400">
                    <CloseCircleOutlined className="text-[10px]" />
                    {remaining} chưa
                  </span>
                </div>
              </div>
            </div>
          );
        })}

        {/* Game Quiz Card (if applicable) */}
        {showGameStats && (
          <div className="flex flex-col justify-between p-3 rounded-xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900/40 hover:border-purple-300 dark:hover:border-purple-700 transition-all shadow-2xs">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2">
                <Tag
                  icon={<PlayCircleOutlined />}
                  color="purple"
                  className="m-0 text-[11px] font-semibold rounded-md"
                >
                  Game Quiz (100%)
                </Tag>

                <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                  {gameRate}%
                </span>
              </div>

              <div className="font-semibold text-xs text-purple-950 dark:text-purple-200 line-clamp-2 min-h-[32px] leading-snug">
                Trắc nghiệm Game hoàn thành 100% câu hỏi
              </div>
            </div>

            <div className="pt-2 mt-2 border-t border-purple-100 dark:border-purple-900/40">
              <Progress
                percent={gameRate}
                showInfo={false}
                strokeColor={{
                  '0%': '#8b5cf6',
                  '100%': '#a855f7',
                }}
                trailColor="#e2e8f0"
                size={['100%', 6]}
                className="!m-0 mb-2"
              />

              <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400 font-medium">
                  <CheckCircleOutlined className="text-[10px]" />
                  <b>{gameSubmittedCount}</b>/{totalAssigned} xong
                </span>
                <span className="flex items-center gap-1 text-gray-400">
                  <CloseCircleOutlined className="text-[10px]" />
                  {Math.max(0, totalAssigned - gameSubmittedCount)} chưa
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
