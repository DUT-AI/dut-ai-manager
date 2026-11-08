import dayjs from 'dayjs';
import type { SubmissionHistoryItem, ExerciseSummary } from '../types/homework.types';
import type { Schema } from '@/types/api';

export type CodingSubmissionDetails = Schema<'CodingSubmissionDetails'>;
export type GameSubmissionDetails = Schema<'GameSubmissionDetails'>;

export interface NormalizedSubmission {
  id: number;
  homeworkId: number;
  userId: number;
  submissionType: 'CODING' | 'GAME';
  exerciseId: string | null;
  exerciseTitle: string | null;
  score: number | null;
  attemptNumber: number;
  submittedAt: string;
  isPassed: boolean;
  source: 'WEBHOOK' | 'MANUAL_SYNC' | 'UNKNOWN';
  filename: string | null;
  correctCount: number | null;
  totalQuestions: number | null;
  codingDetails?: CodingSubmissionDetails | null;
  gameDetails?: GameSubmissionDetails | null;
}

export interface ExerciseGroupSummary {
  exerciseId: string;
  exerciseTitle: string;
  submissions: NormalizedSubmission[];
  attemptCount: number;
  bestScore: number | null;
  latestSubmittedAt: string;
  isPassed: boolean;
}

/**
 * Normalizes a raw SubmissionHistoryItem into a clean, predictable NormalizedSubmission.
 * Direct strongly-typed mapping with ZERO fallback soup.
 */
export function normalizeSubmission(raw: SubmissionHistoryItem): NormalizedSubmission {
  const isCoding = raw.submission_type === 'CODING';
  const details = raw.details;

  let filename: string | null = null;
  let correctCount: number | null = null;
  let totalQuestions: number | null = null;
  let codingDetails: CodingSubmissionDetails | null = null;
  let gameDetails: GameSubmissionDetails | null = null;

  if (isCoding) {
    codingDetails = details as CodingSubmissionDetails;
    filename = codingDetails?.original_filename || null;
  } else {
    gameDetails = details as GameSubmissionDetails;
    correctCount = typeof gameDetails?.correct_count === 'number' ? gameDetails.correct_count : null;
    totalQuestions = typeof gameDetails?.total_questions === 'number' ? gameDetails.total_questions : null;
  }

  // Resolve Source cleanly
  const rawSource = ((details && 'source' in details ? details.source : '') || '').toUpperCase();
  const source: NormalizedSubmission['source'] =
    rawSource.includes('MANUAL') || rawSource.includes('SYNC')
      ? 'MANUAL_SYNC'
      : rawSource.includes('WEBHOOK') || rawSource.includes('REALTIME')
        ? 'WEBHOOK'
        : 'UNKNOWN';

  const score = raw.score ?? (gameDetails?.final_score ?? null);
  const exerciseId = raw.exercise_id ? String(raw.exercise_id) : null;
  const exerciseTitle = raw.exercise_title || (exerciseId ? `Bài tập #${exerciseId.slice(0, 8)}` : null);

  return {
    id: raw.id,
    homeworkId: raw.homework_id,
    userId: raw.user_id,
    submissionType: isCoding ? 'CODING' : 'GAME',
    exerciseId,
    exerciseTitle,
    score,
    attemptNumber: raw.attempt_number || 1,
    submittedAt: raw.submitted_at || '',
    isPassed: raw.is_passed ?? (score !== null ? score >= 5 : true),
    source,
    filename,
    correctCount,
    totalQuestions,
    codingDetails,
    gameDetails,
  };
}

/**
 * Normalizes an array of raw submissions and sorts by submittedAt descending.
 */
export function normalizeSubmissions(rawList?: SubmissionHistoryItem[] | null): NormalizedSubmission[] {
  if (!rawList || !Array.isArray(rawList)) return [];
  return rawList
    .map(normalizeSubmission)
    .sort((a, b) => dayjs(b.submittedAt).valueOf() - dayjs(a.submittedAt).valueOf());
}

/**
 * Groups coding submissions by exercise_id.
 * Strict & Clean:
 * - Only processes submissions with submissionType === 'CODING'.
 * - If allExercises is provided, strictly represents all exercises from the lesson in order.
 */
export function groupSubmissionsByExercise(
  submissions: NormalizedSubmission[],
  allExercises?: ExerciseSummary[] | null
): ExerciseGroupSummary[] {
  // 1. Strict filtering: Only accept CODING submissions
  const codingSubs = (submissions || []).filter((s) => s.submissionType === 'CODING');

  const groupMap = new Map<string, NormalizedSubmission[]>();

  for (const sub of codingSubs) {
    if (!sub.exerciseId) continue;
    const key = sub.exerciseId;
    if (!groupMap.has(key)) {
      groupMap.set(key, []);
    }
    groupMap.get(key)!.push(sub);
  }

  const summaries: ExerciseGroupSummary[] = [];
  const processedKeys = new Set<string>();

  // 2. If allExercises is provided, include all exercises from the lesson in order
  if (allExercises && allExercises.length > 0) {
    for (const ex of allExercises) {
      const key = ex.exercise_id || ex.id;
      if (!key) continue;
      const strKey = String(key);
      processedKeys.add(strKey);

      const subs = groupMap.get(strKey) || [];
      const sortedDesc = [...subs].sort(
        (a, b) => dayjs(b.submittedAt).valueOf() - dayjs(a.submittedAt).valueOf()
      );
      const latest = sortedDesc[0];
      const scores = subs.map((s) => s.score).filter((s): s is number => s !== null);
      const bestScore = scores.length > 0 ? Math.max(...scores) : null;
      const isPassed = subs.some((s) => s.isPassed);

      summaries.push({
        exerciseId: strKey,
        exerciseTitle:
          ex.title ||
          latest?.exerciseTitle ||
          `Bài tập #${strKey.slice(0, 8)}`,
        submissions: sortedDesc,
        attemptCount: subs.length,
        bestScore,
        latestSubmittedAt: latest ? latest.submittedAt : '',
        isPassed,
      });
    }
  } else {
    // 3. Fallback when allExercises is absent: Group existing coding exercises with valid IDs
    for (const [key, subs] of groupMap.entries()) {
      const sortedDesc = [...subs].sort(
        (a, b) => dayjs(b.submittedAt).valueOf() - dayjs(a.submittedAt).valueOf()
      );
      const latest = sortedDesc[0];
      const scores = subs.map((s) => s.score).filter((s): s is number => s !== null);
      const bestScore = scores.length > 0 ? Math.max(...scores) : null;
      const isPassed = subs.some((s) => s.isPassed);

      summaries.push({
        exerciseId: key,
        exerciseTitle:
          latest?.exerciseTitle ||
          `Bài tập #${key.slice(0, 8)}`,
        submissions: sortedDesc,
        attemptCount: subs.length,
        bestScore,
        latestSubmittedAt: latest ? latest.submittedAt : '',
        isPassed,
      });
    }
  }

  return summaries;
}
