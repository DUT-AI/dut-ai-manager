import React from 'react';
import { Card, Tag, Typography } from 'antd';
import {
  CodeOutlined,
  PlayCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { NormalizedSubmission } from '../utils/submissionUtils';

const { Text } = Typography;

export interface SubmissionItemCardProps {
  submission: NormalizedSubmission;
  deadline?: string | null;
  displayIndex?: number;
  showExerciseTitle?: boolean;
}

export const SubmissionItemCard: React.FC<SubmissionItemCardProps> = ({
  submission,
  deadline,
  displayIndex,
  showExerciseTitle = true,
}) => {
  const isCoding = submission.submissionType === 'CODING';
  const subTime = dayjs(submission.submittedAt);
  const deadlineObj = deadline ? dayjs(deadline) : null;
  const isLate = deadlineObj ? subTime.isAfter(deadlineObj) : false;

  return (
    <Card
      size="small"
      className="!rounded-xl border border-gray-100 dark:border-zinc-700/70 shadow-2xs hover:shadow-xs hover:border-indigo-200 dark:hover:border-zinc-600 transition-all mb-3 bg-white dark:bg-zinc-800/90"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
        <div className="flex items-center gap-2">
          <Tag
            icon={isCoding ? <CodeOutlined /> : <PlayCircleOutlined />}
            color={isCoding ? 'blue' : 'purple'}
            className="m-0 font-medium text-xs rounded-md"
          >
            {isCoding ? 'Coding' : 'Game Quiz'}
          </Tag>

          <span className="font-bold text-xs text-gray-800 dark:text-gray-100">
            Lần nộp #{submission.attemptNumber}
          </span>

          {deadlineObj && (
            isLate ? (
              <Tag color="error" className="m-0 text-[10px] font-semibold rounded-md">
                Quá hạn {subTime.from(deadlineObj, true)}
              </Tag>
            ) : (
              <Tag color="success" className="m-0 text-[10px] font-semibold rounded-md">
                Trước hạn {deadlineObj.from(subTime, true)}
              </Tag>
            )
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {submission.isPassed ? (
            <Tag color="success" className="m-0 text-[11px] rounded-md font-medium inline-flex items-center gap-1">
              <CheckOutlined /> Hoàn thành
            </Tag>
          ) : (
            <Tag color="warning" className="m-0 text-[11px] rounded-md font-medium inline-flex items-center gap-1">
              <CloseOutlined /> Chưa đạt
            </Tag>
          )}

          {displayIndex !== undefined && (
            <span className="text-[11px] text-gray-400 font-mono">
              #{displayIndex}
            </span>
          )}
        </div>
      </div>

      {/* Exercise Title Pill (for Coding) */}
      {isCoding && showExerciseTitle && submission.exerciseTitle && (
        <div className="my-2 px-2.5 py-1.5 rounded-lg bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/50 flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-indigo-950 dark:text-indigo-200 truncate flex items-center gap-1.5">
            📝 <span>{submission.exerciseTitle}</span>
          </span>
          {submission.exerciseId && (
            <span className="text-[10px] text-indigo-400 dark:text-indigo-400/80 font-mono">
              ID: {submission.exerciseId.slice(0, 8)}
            </span>
          )}
        </div>
      )}

      {/* Details Box */}
      <div className="mt-2 text-xs bg-gray-50/70 dark:bg-zinc-900/70 p-2.5 rounded-lg border border-gray-100 dark:border-zinc-800 space-y-1.5">
        {submission.score !== null && (
          <div className="flex justify-between items-center text-gray-600 dark:text-gray-300">
            <span>Điểm số:</span>
            <span className="font-bold text-sm text-emerald-600 dark:text-emerald-400">
              {submission.score} <span className="text-xs text-gray-400 font-normal">/ 10</span>
            </span>
          </div>
        )}

        {submission.correctCount !== null && (
          <div className="flex justify-between items-center text-gray-600 dark:text-gray-300">
            <span>Số câu đúng:</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">
              {submission.correctCount}
              {submission.totalQuestions ? ` / ${submission.totalQuestions}` : ''} câu (100%)
            </span>
          </div>
        )}

        {submission.filename && (
          <div className="flex justify-between items-center text-gray-600 dark:text-gray-300">
            <span className="flex items-center gap-1">
              <FileTextOutlined className="text-gray-400" /> Tệp nộp:
            </span>
            <span
              className="font-mono text-xs text-gray-800 dark:text-gray-200 truncate max-w-[220px]"
              title={submission.filename}
            >
              {submission.filename}
            </span>
          </div>
        )}

        <div className="flex justify-between items-center text-gray-600 dark:text-gray-300 pt-0.5 border-t border-gray-100 dark:border-zinc-800/80">
          <span className="text-gray-400 text-[11px]">Nguồn ghi nhận:</span>
          <span className="text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
            {submission.source === 'WEBHOOK'
              ? '⚡ Quiz Webhook (Tự động)'
              : submission.source === 'MANUAL_SYNC'
                ? '🔄 Đồng bộ thủ công'
                : 'Hệ thống'}
          </span>
        </div>
      </div>
    </Card>
  );
};
