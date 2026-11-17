import type { Schema } from '@/types/api';

export const HomeworkStatus = {
  NOT_SUBMITTED: 'NOT_SUBMITTED',
  SUBMITTED: 'SUBMITTED',
  LeaderChecked: 'LEADER_CHECKED',
  FINISHED: 'FINISHED',
} as const;

export type HomeworkStatus = typeof HomeworkStatus[keyof typeof HomeworkStatus];

export type CompletionStatus = Schema<'CompletionStatus'>;
export type TimelinessStatus = Schema<'TimelinessStatus'>;
export type HomeworkFilterStatus = 'all' | 'uncompleted' | 'completed' | 'overdue';

export type Homework = Schema<'HomeworkResponse'>;
export type HomeworkDetail = Schema<'HomeworkResponseDetail'>;

export type MyHomeworksStats = Schema<'MyHomeworksStats'>;
export type MyHomeworksPageResponse = Schema<'MyHomeworksPageResponse'>;
export type MyHomeworkExerciseStatus = Schema<'MyHomeworkExerciseStatusDTO'>;
export type MyHomeworkDetailResponse = Schema<'MyHomeworkDetailResponse'>;

export type HomeworkCreate = Schema<'HomeworkCreate'>;
export type HomeworkUpdate = Schema<'HomeworkUpdate'>;

export type HomeworkReportResponse = Schema<'HomeworkReportResponse'>;
export type HomeworkSubmissionStatus = Schema<'HomeworkSubmissionStatusResponse'>;

export type ExerciseSummary = Schema<'ExerciseSummaryDTO'> & {
  id?: string;
};

export type UserSubmissionInfo = Schema<'UserSubmissionInfo'>;
export type SubmissionHistoryItem = Schema<'HomeworkSubmissionDetailResponse'>;

export type SyncHomeworkResult = Schema<'SyncHomeworkResult'>;
export type SyncMyHomeworksResult = Schema<'SyncMyHomeworksResult'>;
