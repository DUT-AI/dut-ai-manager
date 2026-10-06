import React, { useState, useMemo } from 'react';
import { Timeline, Typography, Empty, Button, Tag } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExportOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { SubmissionHistoryItem } from '../types/homework.types';
import {
  normalizeSubmissions,
  groupSubmissionsByExercise,
  type NormalizedSubmission,
} from '../utils/submissionUtils';
import { SubmissionItemCard } from './SubmissionItemCard';
import { ExerciseProgressOverview } from './ExerciseProgressOverview';

const { Text } = Typography;

export interface UnifiedSubmissionTimelineProps {
  submissions?: SubmissionHistoryItem[] | null;
  type?: 'CODING' | 'GAME';
  deadline?: string | null;
  homeworkLink?: string | null;
  emptyDescription?: React.ReactNode;
  showExerciseOverview?: boolean;
}

export const UnifiedSubmissionTimeline: React.FC<UnifiedSubmissionTimelineProps> = ({
  submissions: rawSubmissions = [],
  type = 'CODING',
  deadline,
  homeworkLink,
  emptyDescription,
  showExerciseOverview = true,
}) => {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | 'all'>('all');

  // Normalize all submissions
  const normalizedList = useMemo(() => {
    return normalizeSubmissions(rawSubmissions);
  }, [rawSubmissions]);

  // Group by Exercise for Coding tasks
  const exerciseGroups = useMemo(() => {
    return groupSubmissionsByExercise(normalizedList);
  }, [normalizedList]);

  // Filtered submissions based on selected exercise
  const filteredSubmissions = useMemo(() => {
    if (selectedExerciseId === 'all') return normalizedList;
    return normalizedList.filter((s) => s.exerciseId === selectedExerciseId);
  }, [normalizedList, selectedExerciseId]);

  const isCoding = type === 'CODING';
  const deadlineObj = deadline ? dayjs(deadline) : null;

  if (normalizedList.length === 0) {
    return (
      <div className="py-8 flex flex-col items-center justify-center">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            emptyDescription || (
              <div className="text-center">
                <Text type="secondary" className="block text-sm mb-1 font-medium">
                  {isCoding
                    ? 'Chưa có lượt nộp bài tập coding nào được ghi nhận'
                    : 'Chưa có lượt chơi game quiz nào đạt 100%'}
                </Text>
                <Text type="secondary" className="text-xs">
                  Kết quả sẽ được tự động đồng bộ ngay sau khi hoàn thành trên hệ thống Quiz.
                </Text>
              </div>
            )
          }
        />
        {homeworkLink && (
          <Button
            type="primary"
            href={homeworkLink}
            target="_blank"
            rel="noopener noreferrer"
            icon={<ExportOutlined />}
            className="mt-4 bg-indigo-600 hover:bg-indigo-700 h-9 font-semibold rounded-lg"
          >
            {isCoding ? 'Làm bài tập Coding trên Quiz' : 'Chơi Game trắc nghiệm ngay'}
          </Button>
        )}
      </div>
    );
  }

  const latest = normalizedList[0];
  const isLatestLate = deadlineObj ? dayjs(latest.submittedAt).isAfter(deadlineObj) : false;
  const isAllPassed = normalizedList.some((s) => s.isPassed);

  return (
    <div className="space-y-4 pt-1">
      {/* Overall Status Banner */}
      <div className="p-3.5 rounded-xl border border-emerald-100 dark:border-emerald-950/60 bg-gradient-to-br from-emerald-50/70 via-teal-50/20 to-white dark:from-emerald-950/30 dark:via-zinc-900 dark:to-zinc-900 shadow-2xs">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-base shadow-2xs">
              <CheckCircleOutlined />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-sm text-gray-900 dark:text-gray-100">
                  {isCoding ? 'Đã ghi nhận bài nộp Coding' : 'Đã hoàn thành Game Quiz (100%)'}
                </span>
                {deadlineObj && (
                  isLatestLate ? (
                    <Tag color="error" className="m-0 text-xs font-semibold rounded-md">
                      Nộp trễ
                    </Tag>
                  ) : (
                    <Tag color="success" className="m-0 text-xs font-semibold rounded-md">
                      Đúng hạn
                    </Tag>
                  )
                )}
              </div>
              <Text type="secondary" className="text-xs block mt-0.5">
                Gần nhất: {dayjs(latest.submittedAt).format('DD/MM/YYYY HH:mm:ss')} ({dayjs(latest.submittedAt).fromNow()})
              </Text>
            </div>
          </div>

          <Tag color="blue" className="m-0 font-semibold text-xs px-2.5 py-0.5 rounded-full">
            {normalizedList.length} lần nộp
          </Tag>
        </div>
      </div>

      {/* Exercise Matrix Overview (if Coding and multiple exercises found) */}
      {showExerciseOverview && isCoding && exerciseGroups.length > 0 && (
        <ExerciseProgressOverview
          exercises={exerciseGroups}
          selectedExerciseId={selectedExerciseId}
          onSelectExercise={setSelectedExerciseId}
        />
      )}

      {/* Timeline Section Header */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-1.5">
            <HistoryOutlined className="text-gray-400 text-xs" />
            <Text className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
              Lịch sử các lần nộp ({filteredSubmissions.length})
            </Text>
          </div>

          {homeworkLink && (
            <Button
              type="link"
              href={homeworkLink}
              target="_blank"
              rel="noopener noreferrer"
              icon={<ExportOutlined />}
              size="small"
              className="p-0 text-xs text-indigo-600 dark:text-indigo-400 font-semibold"
            >
              Làm lại trên Quiz
            </Button>
          )}
        </div>

        {/* Timeline of Submissions */}
        <Timeline
          mode="left"
          items={filteredSubmissions.map((sub: NormalizedSubmission, idx: number) => {
            const subTime = dayjs(sub.submittedAt);
            const displayIdx = filteredSubmissions.length - idx;

            return {
              color: sub.submissionType === 'CODING' ? '#4f46e5' : '#8b5cf6',
              label: (
                <div className="text-right pr-2">
                  <div className="font-semibold text-xs text-gray-700 dark:text-gray-300">
                    {subTime.format('DD/MM/YYYY')}
                  </div>
                  <div className="text-[11px] text-gray-400">
                    {subTime.format('HH:mm:ss')}
                  </div>
                </div>
              ),
              children: (
                <SubmissionItemCard
                  submission={sub}
                  deadline={deadline}
                  displayIndex={displayIdx}
                  showExerciseTitle={selectedExerciseId === 'all'}
                />
              ),
            };
          })}
        />
      </div>
    </div>
  );
};
