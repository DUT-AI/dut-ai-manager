import type { Schema } from '@/types/api';

export const HomeworkStatus = {
  NOT_SUBMITTED: 'NOT_SUBMITTED',
  SUBMITTED: 'SUBMITTED',
  LeaderChecked: 'LEADER_CHECKED',
  FINISHED: 'FINISHED',
} as const;

export type HomeworkStatus = typeof HomeworkStatus[keyof typeof HomeworkStatus];

export type Homework = Schema<'HomeworkResponse'> & {
  coding_status?: 'COMPLETED' | 'PARTIALLY_SUBMITTED' | 'NOT_SUBMITTED';
  total_coding_required?: number;
  total_coding_completed?: number;
};
export type HomeworkDetail = Schema<'HomeworkResponseDetail'>;

export type HomeworkCreate = Schema<'HomeworkCreate'>;
export type HomeworkUpdate = Schema<'HomeworkUpdate'>;

export type HomeworkReportResponse = Schema<'HomeworkReportResponse'>;
export type HomeworkSubmissionStatus = Schema<'HomeworkSubmissionStatusResponse'> & {
  total_completed_count?: number;
};

export type ExerciseSummary = Schema<'ExerciseSummaryDTO'> & {
  id?: string;
};

export type UserSubmissionInfo = Schema<'UserSubmissionInfo'>;

export type SubmissionHistoryItem = Schema<'HomeworkSubmissionDetailResponse'>;

export type SyncHomeworkResult = Schema<'SyncHomeworkResult'>;
