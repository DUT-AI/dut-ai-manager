import { useMemo } from 'react';
import type {
  Homework,
  HomeworkDetail,
  HomeworkSubmissionStatus,
  UserSubmissionInfo,
} from '../types/homework.types';

export interface CategoryStatus {
  submitted: UserSubmissionInfo[];
  not_submitted: UserSubmissionInfo[];
}

export interface HomeworkSubmissionMetrics {
  hasCoding: boolean;
  hasGame: boolean;
  codingStatus: CategoryStatus;
  gameStatus: CategoryStatus;
  codingSubmittedCount: number;
  codingTotalCount: number;
  gameSubmittedCount: number;
  gameTotalCount: number;
  totalSubmitted: number;
  totalAssigned: number;
  submissionPercent: number;
}

type HomeworkRequirementsSource =
  | Pick<Homework, 'requires_coding' | 'requires_game'>
  | Pick<HomeworkDetail, 'requires_coding' | 'requires_game' | 'assignee_ids'>
  | null
  | undefined;

const EMPTY_CATEGORY_STATUS: CategoryStatus = {
  submitted: [],
  not_submitted: [],
};

/**
 * Computes submission metrics (coding, game, overall progress) directly from backend SSOT fields.
 */
export function useHomeworkSubmissionMetrics(
  homework: HomeworkRequirementsSource,
  statusData: HomeworkSubmissionStatus | null | undefined,
): HomeworkSubmissionMetrics {
  return useMemo(() => {
    const hasCoding = homework?.requires_coding ?? true;
    const hasGame = homework?.requires_game ?? false;

    const codingStatus = statusData?.coding ?? EMPTY_CATEGORY_STATUS;
    const gameStatus = statusData?.game ?? EMPTY_CATEGORY_STATUS;

    const codingSubmittedCount = codingStatus.submitted.length;
    const codingTotalCount = codingSubmittedCount + codingStatus.not_submitted.length;

    const gameSubmittedCount = gameStatus.submitted.length;
    const gameTotalCount = gameSubmittedCount + gameStatus.not_submitted.length;

    const totalSubmitted = statusData?.total_completed_count ?? 0;
    const assigneeCount =
      homework && 'assignee_ids' in homework ? (homework.assignee_ids?.length ?? 0) : 0;
    const totalAssigned = statusData?.students?.length ?? assigneeCount;

    const submissionPercent =
      totalAssigned > 0 ? Math.round((totalSubmitted / totalAssigned) * 100) : 0;

    return {
      hasCoding,
      hasGame,
      codingStatus,
      gameStatus,
      codingSubmittedCount,
      codingTotalCount,
      gameSubmittedCount,
      gameTotalCount,
      totalSubmitted,
      totalAssigned,
      submissionPercent,
    };
  }, [homework, statusData]);
}
