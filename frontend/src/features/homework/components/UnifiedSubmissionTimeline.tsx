import React, { useState, useMemo } from 'react';
import { Timeline, Typography, Empty, Button, Tag } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExportOutlined,
  HistoryOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { SubmissionHistoryItem, ExerciseSummary } from '../types/homework.types';
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
  allExercises?: ExerciseSummary[] | null;
}

export const UnifiedSubmissionTimeline: React.FC<UnifiedSubmissionTimelineProps> = ({
  submissions: rawSubmissions = [],
  type = 'CODING',
  deadline,
  homeworkLink,
  emptyDescription,
  showExerciseOverview = true,
  allExercises,
}) => {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | 'all'>('all');

  // Normalize all submissions
  const normalizedList = useMemo(() => {
    return normalizeSubmissions(rawSubmissions);
  }, [rawSubmissions]);

  // Group by Exercise for Coding tasks
  const exerciseGroups = useMemo(() => {
    return groupSubmissionsByExercise(normalizedList, allExercises);
  }, [normalizedList, allExercises]);

  // Filtered submissions based on selected exercise
  const filteredSubmissions = useMemo(() => {
    if (selectedExerciseId === 'all') return normalizedList;
    return normalizedList.filter((s) => s.exerciseId === selectedExerciseId);
  }, [normalizedList, selectedExerciseId]);

  const isCoding = type === 'CODING';
  const deadlineObj = deadline ? dayjs(deadline) : null;
  const hasExercises = exerciseGroups.length > 0;
  const completedExerciseCount = useMemo(() => {
    return exerciseGroups.filter((e) => e.isPassed).length;
  }, [exerciseGroups]);
  const totalExercisesCount = exerciseGroups.length;

  const selectedExercise = useMemo(() => {
    if (selectedExerciseId === 'all') return null;
    return exerciseGroups.find((e) => e.exerciseId === selectedExerciseId);
  }, [exerciseGroups, selectedExerciseId]);

  // Pure empty state when there are NO submissions AND NO exercises structure
  if (normalizedList.length === 0 && !hasExercises) {
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
  const isLatestLate = deadlineObj && latest ? dayjs(latest.submittedAt).isAfter(deadlineObj) : false;
  const isAllCompleted = totalExercisesCount > 0 && completedExerciseCount === totalExercisesCount;

  return (
    <div className="space-y-4 pt-1">
      {/* Overall Status Banner */}
      {normalizedList.length === 0 ? (
        <div className="p-3.5 rounded-xl border border-rose-100 dark:border-rose-950/60 bg-gradient-to-br from-rose-50/60 via-orange-50/20 to-white dark:from-rose-950/30 dark:via-zinc-900 dark:to-zinc-900 shadow-2xs">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-rose-100 dark:bg-rose-950/80 text-rose-600 dark:text-rose-400 flex items-center justify-center text-base shadow-2xs">
                <CloseCircleOutlined />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-sm text-gray-900 dark:text-gray-100">
                    Chưa có bài nộp nào được ghi nhận
                  </span>
                  <Tag color="error" className="m-0 text-xs font-semibold rounded-md">
                    Chưa nộp
                  </Tag>
                </div>
                <Text type="secondary" className="text-xs block mt-0.5">
                  Học viên chưa hoàn thành bài tập nào trong số {totalExercisesCount} bài con của bài học này.
                </Text>
              </div>
            </div>

            <Tag color="default" className="m-0 font-semibold text-xs px-2.5 py-0.5 rounded-full">
              0/{totalExercisesCount} bài
            </Tag>
          </div>
        </div>
      ) : (
        <div
          className={`p-3.5 rounded-xl border shadow-2xs ${
            isAllCompleted
              ? 'border-emerald-100 dark:border-emerald-950/60 bg-gradient-to-br from-emerald-50/70 via-teal-50/20 to-white dark:from-emerald-950/30 dark:via-zinc-900 dark:to-zinc-900'
              : 'border-indigo-100 dark:border-indigo-950/60 bg-gradient-to-br from-indigo-50/60 via-purple-50/20 to-white dark:from-indigo-950/30 dark:via-zinc-900 dark:to-zinc-900'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center text-base shadow-2xs ${
                  isAllCompleted
                    ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400'
                    : 'bg-indigo-100 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400'
                }`}
              >
                {isAllCompleted ? <CheckCircleOutlined /> : <HistoryOutlined />}
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-sm text-gray-900 dark:text-gray-100">
                    {isAllCompleted
                      ? (isCoding ? 'Đã hoàn thành tất cả bài tập Coding' : 'Đã hoàn thành Game Quiz (100%)')
                      : (isCoding ? `Đã làm ${completedExerciseCount}/${totalExercisesCount} bài tập con` : 'Đã ghi nhận bài nộp')}
                  </span>
                  {deadlineObj &&
                    (isLatestLate ? (
                      <Tag color="error" className="m-0 text-xs font-semibold rounded-md">
                        Nộp trễ
                      </Tag>
                    ) : (
                      <Tag color="success" className="m-0 text-xs font-semibold rounded-md">
                        Đúng hạn
                      </Tag>
                    ))}
                </div>
                {latest && (
                  <Text type="secondary" className="text-xs block mt-0.5">
                    Gần nhất: {dayjs(latest.submittedAt).format('DD/MM/YYYY HH:mm:ss')} ({dayjs(latest.submittedAt).fromNow()})
                  </Text>
                )}
              </div>
            </div>

            <Tag color={isAllCompleted ? 'green' : 'blue'} className="m-0 font-semibold text-xs px-2.5 py-0.5 rounded-full">
              {normalizedList.length} lần nộp ({completedExerciseCount}/{totalExercisesCount} bài)
            </Tag>
          </div>
        </div>
      )}

      {/* Exercise Matrix Overview (Shows ALL sub-exercises of the lesson) */}
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

        {/* Timeline of Submissions or Missing Exercise Notice */}
        {filteredSubmissions.length === 0 ? (
          <div className="p-8 my-3 rounded-2xl border border-dashed border-gray-200 dark:border-zinc-700 bg-gray-50/50 dark:bg-zinc-900/40 text-center space-y-2">
            <div className="w-10 h-10 mx-auto rounded-full bg-amber-50 dark:bg-amber-950/60 text-amber-500 flex items-center justify-center text-lg">
              <ExclamationCircleOutlined />
            </div>
            <div className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              {selectedExercise ? 'Học viên chưa nộp bài tập này' : 'Chưa có lịch sử nộp bài'}
            </div>
            <div className="text-xs text-gray-400 max-w-md mx-auto">
              {selectedExercise
                ? `Học viên chưa gửi bài nộp nào cho "${selectedExercise.exerciseTitle}".`
                : 'Chưa có bản ghi nộp bài nào được ghi nhận từ hệ thống Quiz.'}
            </div>
          </div>
        ) : (
          <div className="submission-timeline-wrapper pt-2">
            <Timeline
              mode="left"
              items={filteredSubmissions.map((sub: NormalizedSubmission, idx: number) => {
                const subTime = dayjs(sub.submittedAt);
                const displayIdx = filteredSubmissions.length - idx;

                return {
                  color: sub.submissionType === 'CODING' ? '#4f46e5' : '#8b5cf6',
                  label: (
                    <div className="text-right pr-3 whitespace-nowrap min-w-[105px]">
                      <div className="font-semibold text-xs text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {subTime.format('DD/MM/YYYY')}
                      </div>
                      <div className="text-[11px] text-gray-400 whitespace-nowrap font-mono">
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
        )}
      </div>
    </div>
  );
};

