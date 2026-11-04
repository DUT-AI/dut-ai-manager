import { useMemo } from 'react';
import { useAuth } from '@/features/auth/context/AuthContext';
import type { MeetingDetailResponse, ParticipantResponse } from '../types/meeting.types';

export interface MeetingPermissions {
  isTrainer: boolean;
  isTrainee: boolean;
  isCreator: boolean;
  canEvaluateTrainer: boolean;
  myParticipantRecord: ParticipantResponse | null;
  currentUserId: number | undefined;
}

export function useMeetingPermissions(
  meeting: MeetingDetailResponse | null | undefined
): MeetingPermissions {
  const { user } = useAuth();
  const currentUserId = user?.id;

  return useMemo(() => {
    if (!meeting || !currentUserId) {
      return {
        isTrainer: false,
        isTrainee: false,
        isCreator: false,
        canEvaluateTrainer: false,
        myParticipantRecord: null,
        currentUserId,
      };
    }

    const isCreator = meeting.created_by != null && Number(currentUserId) === Number(meeting.created_by);
    const isTrainerInList = (meeting.trainers || []).some(
      (t) => Number(t.user_id) === Number(currentUserId)
    );
    const hasAdminRole = user.role_names?.some((r) =>
      ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())
    ) ?? false;

    const isTrainer = Boolean(isCreator || isTrainerInList || hasAdminRole);
    const myParticipantRecord =
      (meeting.trainees || []).find((p) => Number(p.user_id) === Number(currentUserId)) || null;
    const isTrainee = Boolean(myParticipantRecord);

    const isEvaluationOpen = Boolean(meeting.enable_evaluation);
    const canEvaluateTrainer = isTrainee && isEvaluationOpen;

    return {
      isTrainer,
      isTrainee,
      isCreator,
      canEvaluateTrainer,
      myParticipantRecord,
      currentUserId,
    };
  }, [meeting, user, currentUserId]);
}
