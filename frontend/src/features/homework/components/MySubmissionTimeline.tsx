import React from 'react';
import type { SubmissionHistoryItem } from '../types/homework.types';
import { UnifiedSubmissionTimeline } from './UnifiedSubmissionTimeline';

export interface MySubmissionTimelineProps {
  submissions?: SubmissionHistoryItem[] | null;
  type: 'CODING' | 'GAME';
  deadline: string;
  homeworkLink?: string | null;
}

/**
 * Clean, modern submission timeline for student's personal view.
 * Powered by the UnifiedSubmissionTimeline engine.
 */
export const MySubmissionTimeline: React.FC<MySubmissionTimelineProps> = ({
  submissions,
  type,
  deadline,
  homeworkLink,
}) => {
  return (
    <UnifiedSubmissionTimeline
      submissions={submissions}
      type={type}
      deadline={deadline}
      homeworkLink={homeworkLink}
      showExerciseOverview={type === 'CODING'}
    />
  );
};
