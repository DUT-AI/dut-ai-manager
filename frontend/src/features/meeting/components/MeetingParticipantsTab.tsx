import React, { useState, useMemo } from 'react';
import dayjs from 'dayjs';
import type {
  ParticipantResponse,
  UpdateParticipantStatusPayload,
  EvaluationResponse,
} from '../types/meeting.types';
import { ParticipantStatus } from '../types/meeting.types';
import {
  useMeetingDetail,
  useUpdateParticipantStatus,
  useMeetingEvaluationSummary,
} from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { MeetingBatchCheckInBanner } from './MeetingBatchCheckInBanner';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';
import { TrainerEvaluationModal } from './TrainerEvaluationModal';
import { TraineeEvaluationModal } from './TraineeEvaluationModal';
import { MyEvaluationResultModal } from './MyEvaluationResultModal';
import {
  EvaluationProgressFilterBar,
  TraineeEvaluationCard,
  ParticipantListTable,
  ParticipantMobileList,
} from './participants';

interface Props {
  meetingId: number;
}

export const MeetingParticipantsTab: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();

  // Local Modal States
  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [isEditStatusModalOpen, setIsEditStatusModalOpen] = useState(false);
  const [evaluatingParticipant, setEvaluatingParticipant] = useState<ParticipantResponse | null>(null);
  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);
  const [evalFilter, setEvalFilter] = useState<'all' | 'unrated' | 'rated'>('all');

  const updateParticipantStatusMutation = useUpdateParticipantStatus();
  const { data: evalSummary, refetch: refetchEvalSummary } = useMeetingEvaluationSummary(
    meetingId,
    Boolean(meeting?.enable_evaluation)
  );

  const currentUserId = user?.id;
  const isTrainer = Boolean(
    (meeting?.created_by != null && currentUserId != null && Number(currentUserId) === Number(meeting.created_by)) ||
    (meeting?.trainer?.id != null && currentUserId != null && Number(currentUserId) === Number(meeting.trainer.id)) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false)
  );

  const isEnded = meeting ? dayjs().isAfter(dayjs(meeting.end_time)) : false;
  const totalParticipants = meeting?.participants?.length || 0;

  // Build evaluation mappings & count stats
  const {
    trainerEvalsByTraineeId,
    traineeEvalsByReviewerId,
    myEvalForTrainer,
    isCurrentUserTrainee,
    trainees,
    trainerEvaluatedCount,
    traineeEvaluatedCount,
  } = useMemo(() => {
    const trainerMap = new Map<number, EvaluationResponse>();
    const traineeMap = new Map<number, EvaluationResponse>();

    if (evalSummary?.evaluations) {
      evalSummary.evaluations.forEach((e) => {
        if (e.evaluation_type === 'TRAINER_TO_TRAINEE') {
          trainerMap.set(e.target_user_id, e);
        } else if (e.evaluation_type === 'TRAINEE_TO_TRAINER' && e.reviewer_id) {
          traineeMap.set(e.reviewer_id, e);
        }
      });
    }

    const allTrainees = (meeting?.participants || []).filter(
      (p) => p.user_id !== meeting?.created_by && p.user_id !== meeting?.trainer?.id
    );

    const activeTrainees = allTrainees.filter(
      (p) =>
        p.status !== ParticipantStatus.ABSENT_EXCUSED &&
        p.status !== ParticipantStatus.ABSENT_UNEXCUSED
    );

    const trainerCount = activeTrainees.filter((p) => trainerMap.has(p.user_id)).length;
    const traineeCount = activeTrainees.filter((p) => traineeMap.has(p.user_id)).length;

    const myEval = evalSummary?.my_evaluation || (currentUserId ? traineeMap.get(currentUserId) : null);
    if (myEval && currentUserId && !traineeMap.has(currentUserId)) {
      traineeMap.set(currentUserId, myEval);
    }
    const isTrainee = allTrainees.some((p) => p.user_id === currentUserId);

    return {
      trainerEvalsByTraineeId: trainerMap,
      traineeEvalsByReviewerId: traineeMap,
      myEvalForTrainer: myEval,
      isCurrentUserTrainee: isTrainee,
      trainees: activeTrainees,
      trainerEvaluatedCount: trainerCount,
      traineeEvaluatedCount: traineeCount,
    };
  }, [evalSummary, meeting, currentUserId]);

  if (!meeting) return null;

  const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
    if (!editingParticipant) return;
    await updateParticipantStatusMutation.mutateAsync({
      meetingId: meeting.id,
      userId: editingParticipant.user_id,
      payload,
    });
    refetch();
  };

  // Filter participants based on evaluation filter
  const filteredParticipants = (meeting.participants || []).filter((p) => {
    if (!meeting.enable_evaluation || evalFilter === 'all') return true;
    const isEvaluated = trainerEvalsByTraineeId.has(p.user_id);
    if (evalFilter === 'rated') return isEvaluated;
    if (evalFilter === 'unrated') {
      const isAbsent =
        p.status === ParticipantStatus.ABSENT_EXCUSED ||
        p.status === ParticipantStatus.ABSENT_UNEXCUSED;
      const isMeetingCreator = p.user_id === meeting.created_by;
      return !isEvaluated && !isAbsent && !isMeetingCreator;
    }
    return true;
  });

  const totalActiveTrainees = trainees.length;
  const unratedCount = Math.max(0, totalActiveTrainees - trainerEvaluatedCount);

  return (
    <div className="space-y-4">
      {/* Batch Check-in Banner */}
      <MeetingBatchCheckInBanner meetingId={meetingId} />

      {/* Trainee Banner for Self-Evaluation */}
      {meeting.enable_evaluation && isCurrentUserTrainee && (
        <TraineeEvaluationCard
          myEvalForTrainer={myEvalForTrainer}
          onOpenMyResult={() => setIsMyResultOpen(true)}
          onOpenTraineeEval={() => setIsTraineeEvalOpen(true)}
        />
      )}

      {/* Evaluation Progress & Filter Bar */}
      {meeting.enable_evaluation && (
        <EvaluationProgressFilterBar
          totalParticipants={totalParticipants}
          totalActiveTrainees={totalActiveTrainees}
          trainerEvaluatedCount={trainerEvaluatedCount}
          traineeEvaluatedCount={traineeEvaluatedCount}
          unratedCount={unratedCount}
          evalFilter={evalFilter}
          onFilterChange={setEvalFilter}
        />
      )}

      {/* Participants Content: Mobile List vs Desktop Table */}
      <div className="block md:hidden">
        <ParticipantMobileList
          meeting={meeting}
          participants={filteredParticipants}
          currentUserId={currentUserId}
          isTrainer={isTrainer}
          isEnded={isEnded}
          trainerEvalsByTraineeId={trainerEvalsByTraineeId}
          traineeEvalsByReviewerId={traineeEvalsByReviewerId}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
          onEvaluate={(p) => setEvaluatingParticipant(p)}
        />
      </div>

      <div className="hidden md:block">
        <ParticipantListTable
          meeting={meeting}
          participants={filteredParticipants}
          currentUserId={currentUserId}
          isTrainer={isTrainer}
          isEnded={isEnded}
          trainerEvalsByTraineeId={trainerEvalsByTraineeId}
          traineeEvalsByReviewerId={traineeEvalsByReviewerId}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
          onEvaluate={(p) => setEvaluatingParticipant(p)}
        />
      </div>

      {/* Modals with isolated open states */}
      <EditParticipantStatusModal
        open={isEditStatusModalOpen}
        participant={editingParticipant}
        onClose={() => {
          setIsEditStatusModalOpen(false);
          setEditingParticipant(null);
        }}
        onSubmit={handleUpdateStatus}
        loading={updateParticipantStatusMutation.isPending}
      />

      {evaluatingParticipant && (
        <TrainerEvaluationModal
          open={!!evaluatingParticipant}
          meetingId={meeting.id}
          trainee={evaluatingParticipant}
          existingEvaluation={trainerEvalsByTraineeId.get(evaluatingParticipant.user_id)}
          participants={meeting.participants}
          onSelectTrainee={(p) => setEvaluatingParticipant(p)}
          onSuccess={() => {
            setEvaluatingParticipant(null);
            refetch();
            refetchEvalSummary();
          }}
          onClose={() => setEvaluatingParticipant(null)}
          onCancel={() => setEvaluatingParticipant(null)}
        />
      )}

      <TraineeEvaluationModal
        open={isTraineeEvalOpen}
        meetingId={meeting.id}
        trainerId={meeting.trainer?.id || meeting.created_by || undefined}
        trainerName={meeting.trainer?.name}
        trainerAvatarUrl={meeting.trainer?.avatar_url}
        existingEvaluation={myEvalForTrainer}
        onSuccess={() => {
          setIsTraineeEvalOpen(false);
          refetch();
          refetchEvalSummary();
        }}
        onClose={() => setIsTraineeEvalOpen(false)}
        onCancel={() => setIsTraineeEvalOpen(false)}
      />

      <MyEvaluationResultModal
        open={isMyResultOpen}
        meetingId={meeting.id}
        onClose={() => setIsMyResultOpen(false)}
      />
    </div>
  );
};
