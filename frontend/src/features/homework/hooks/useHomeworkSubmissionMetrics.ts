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

function pickByRequirements(
  hasCoding: boolean,
  hasGame: boolean,
  codingValue: number,
  gameValue: number,
): number {
  if (hasCoding && !hasGame) return codingValue;
  if (!hasCoding && hasGame) return gameValue;
  return Math.max(codingValue, gameValue);
}

function resolveTotalSubmitted(
  statusData: HomeworkSubmissionStatus | null | undefined,
  hasCoding: boolean,
  hasGame: boolean,
  codingSubmittedCount: number,
  gameSubmittedCount: number,
): number {
  if (statusData?.total_completed_count != null) {
    return statusData.total_completed_count;
  }

  return pickByRequirements(hasCoding, hasGame, codingSubmittedCount, gameSubmittedCount);
}

function resolveTotalAssigned(
  homework: HomeworkRequirementsSource,
  statusData: HomeworkSubmissionStatus | null | undefined,
  hasCoding: boolean,
  hasGame: boolean,
  codingTotalCount: number,
  gameTotalCount: number,
): number {
  if (statusData?.students?.length) {
    return statusData.students.length;
  }

  const assigneeIds = homework && 'assignee_ids' in homework ? homework.assignee_ids : undefined;
  if (assigneeIds?.length) {
    return assigneeIds.length;
  }

  return pickByRequirements(hasCoding, hasGame, codingTotalCount, gameTotalCount);
}

/**
 * Computes submission metrics (coding, game, overall progress) from a homework and its submission status.
 * Prefers backend SSOT aggregates (`total_completed_count`, `students`) and falls back to category counts.
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

    const totalSubmitted = resolveTotalSubmitted(
      statusData,
      hasCoding,
      hasGame,
      codingSubmittedCount,
      gameSubmittedCount,
    );

    const totalAssigned = resolveTotalAssigned(
      homework,
      statusData,
      hasCoding,
      hasGame,
      codingTotalCount,
      gameTotalCount,
    );

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
