import dayjs from 'dayjs';
import type { SubmissionHistoryItem } from '../types/homework.types';

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
  rawDetails: Record<string, any>;
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
 * Eliminates all fallback soup (sub.details vs sub.metadata vs top-level fields).
 */
export function normalizeSubmission(raw: SubmissionHistoryItem): NormalizedSubmission {
  const details = raw.details || raw.metadata || {};
  
  // Resolve Score: prioritize top-level score, then details.final_score
  let score: number | null = null;
  if (typeof raw.score === 'number') {
    score = raw.score;
  } else if (typeof details.final_score === 'number') {
    score = details.final_score;
  } else if (typeof details.score === 'number') {
    score = details.score;
  }

  // Resolve Attempt Number
  const attemptNumber = raw.attempt_number ?? details.attempt_number ?? 1;

  // Resolve Exercise ID & Title
  const exerciseId = raw.exercise_id ?? details.exercise_id ?? null;
  const exerciseTitle = raw.exercise_title ?? details.exercise_title ?? (exerciseId ? `Bài tập #${String(exerciseId).slice(0, 8)}` : null);

  // Resolve Source
  const rawSource = (raw.source || details.source || '').toUpperCase();
  const source: NormalizedSubmission['source'] =
    rawSource.includes('MANUAL') || rawSource.includes('SYNC')
      ? 'MANUAL_SYNC'
      : rawSource.includes('WEBHOOK') || rawSource.includes('REALTIME')
        ? 'WEBHOOK'
        : 'UNKNOWN';

  // Resolve Game Quiz metrics
  const correctCount = typeof details.correct_count === 'number' ? details.correct_count : null;
  const totalQuestions = typeof details.total_questions === 'number' ? details.total_questions : null;

  // Resolve filename
  const filename = details.original_filename || details.filename || null;

  return {
    id: raw.id,
    homeworkId: raw.homework_id,
    userId: raw.user_id,
    submissionType: raw.submission_type,
    exerciseId: exerciseId ? String(exerciseId) : null,
    exerciseTitle,
    score,
    attemptNumber,
    submittedAt: raw.submitted_at,
    isPassed: raw.is_passed ?? (score !== null ? score >= 5 : true),
    source,
    filename,
    correctCount,
    totalQuestions,
    rawDetails: details,
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
 * Groups submissions by exercise_id. Useful for Coding homeworks with multiple exercises.
 */
export function groupSubmissionsByExercise(submissions: NormalizedSubmission[]): ExerciseGroupSummary[] {
  const groupMap = new Map<string, NormalizedSubmission[]>();

  for (const sub of submissions) {
    const key = sub.exerciseId || '__general__';
    if (!groupMap.has(key)) {
      groupMap.set(key, []);
    }
    groupMap.get(key)!.push(sub);
  }

  const summaries: ExerciseGroupSummary[] = [];

  for (const [key, subs] of groupMap.entries()) {
    // Sort chronological ascending within group to find best score and stats
    const sortedDesc = [...subs].sort((a, b) => dayjs(b.submittedAt).valueOf() - dayjs(a.submittedAt).valueOf());
    const latest = sortedDesc[0];
    
    // Compute best score
    const scores = subs.map((s) => s.score).filter((s): s is number => s !== null);
    const bestScore = scores.length > 0 ? Math.max(...scores) : null;
    const isPassed = subs.some((s) => s.isPassed);

    summaries.push({
      exerciseId: key,
      exerciseTitle: latest.exerciseTitle || (key === '__general__' ? 'Bài tập chung' : `Bài tập #${key.slice(0, 8)}`),
      submissions: sortedDesc,
      attemptCount: subs.length,
      bestScore,
      latestSubmittedAt: latest.submittedAt,
      isPassed,
    });
  }

  return summaries;
}
