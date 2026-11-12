import React, { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import type {
  ParticipantResponse,
  UpdateParticipantStatusPayload,
  EvaluationResponse,
  MeetingOverallEvaluationResponse,
} from '../types/meeting.types';
import { ParticipantStatus } from '../types/meeting.types';
import {
  useMeetingDetail,
  useUpdateParticipantStatus,
  useMeetingEvaluationSummary,
} from '../hooks/useMeetings';
import { useMeetingPermissions } from '../hooks/useMeetingPermissions';
import { useAuth } from '@/features/auth/context/AuthContext';
import { MeetingBatchCheckInBanner } from './MeetingBatchCheckInBanner';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';
import { EvaluationDetailModal } from './EvaluationDetailModal';
import {
  EvaluationProgressFilterBar,
  TraineeEvaluationCard,
  TrainerListTable,
  TraineeListTable,
  ParticipantMobileList,
} from './participants';

interface Props {
  meetingId: number;
  onOpenTraineeEvaluation?: () => void;
  onOpenOverallEvaluation?: () => void;
  overallEval?: MeetingOverallEvaluationResponse | null;
}

export const MeetingParticipantsTab: React.FC<Props> = ({
  meetingId,
  onOpenTraineeEvaluation,
  onOpenOverallEvaluation,
  overallEval,
}) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();

  // Local Modal States
  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [isEditStatusModalOpen, setIsEditStatusModalOpen] = useState(false);
  const [evalFilter, setEvalFilter] = useState<'all' | 'unrated' | 'rated'>('all');
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationResponse | null>(null);
  const [isEvaluationDetailModalOpen, setIsEvaluationDetailModalOpen] = useState(false);

  const updateParticipantStatusMutation = useUpdateParticipantStatus();
  const { data: evalSummary, refetch: refetchEvalSummary } = useMeetingEvaluationSummary(
    meetingId,
    Boolean(meeting?.enable_evaluation)
  );

  const currentUserId = user?.id;
  const { isTrainer } = useMeetingPermissions(meeting);

  const isEnded = meeting ? dayjs().isAfter(dayjs(meeting.end_time)) : false;
  const trainerParticipants = meeting?.trainers || [];
  const traineeParticipants = meeting?.trainees || [];
  const totalParticipants = trainerParticipants.length + traineeParticipants.length;

  // Build evaluation mappings & count stats cho học viên
  const {
    traineeEvalsByReviewerId,
    myEvalForTrainer,
    isCurrentUserTrainee,
    activeTrainees,
    traineeEvaluatedCount,
  } = useMemo(() => {
    const traineeMap = new Map<number, EvaluationResponse>();

    if (evalSummary?.evaluations) {
      evalSummary.evaluations.forEach((e) => {
        if (e.evaluation_type === 'TRAINEE_TO_TRAINER' && e.reviewer_id) {
          traineeMap.set(e.reviewer_id, e);
        }
      });
    }

    const activeList = traineeParticipants.filter(
      (p) =>
        p.status !== ParticipantStatus.ABSENT_EXCUSED &&
        p.status !== ParticipantStatus.ABSENT_UNEXCUSED
    );

    const traineeCount = activeList.filter((p) => traineeMap.has(p.user_id)).length;

    const myEval = evalSummary?.my_evaluation || (currentUserId ? traineeMap.get(currentUserId) : null);
    if (myEval && currentUserId && !traineeMap.has(currentUserId)) {
      traineeMap.set(currentUserId, myEval);
    }
    const isTrainee = traineeParticipants.some((p) => p.user_id === currentUserId);

    return {
      traineeEvalsByReviewerId: traineeMap,
      myEvalForTrainer: myEval,
      isCurrentUserTrainee: isTrainee,
      activeTrainees: activeList,
      traineeEvaluatedCount: traineeCount,
    };
  }, [evalSummary, traineeParticipants, currentUserId]);

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

  // Filter trainees based on evaluation filter
  const filteredTrainees = traineeParticipants.filter((p) => {
    if (!meeting.enable_evaluation || evalFilter === 'all') return true;
    const isEvaluated = traineeEvalsByReviewerId.has(p.user_id);
    if (evalFilter === 'rated') return isEvaluated;
    if (evalFilter === 'unrated') {
      const isAbsent =
        p.status === ParticipantStatus.ABSENT_EXCUSED ||
        p.status === ParticipantStatus.ABSENT_UNEXCUSED;
      return !isEvaluated && !isAbsent;
    }
    return true;
  });

  const totalActiveTrainees = activeTrainees.length;
  const unratedCount = Math.max(0, totalActiveTrainees - traineeEvaluatedCount);

  const handleViewEvaluation = (evaluation: EvaluationResponse) => {
    setSelectedEvaluation(evaluation);
    setIsEvaluationDetailModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Batch Check-in Banner */}
      <MeetingBatchCheckInBanner meetingId={meetingId} />

      {/* Trainee Banner for Self-Evaluation */}
      {meeting.enable_evaluation && isCurrentUserTrainee && (
        <TraineeEvaluationCard
          myEvalForTrainer={myEvalForTrainer}
          onOpenTraineeEval={onOpenTraineeEvaluation || (() => { })}
        />
      )}

      {/* Section 1: Bảng Giảng viên / Người phụ trách (Desktop) */}
      <div className="hidden md:block mt-3">
        <TrainerListTable
          meeting={meeting}
          trainers={trainerParticipants}
          currentUserId={currentUserId}
          isTrainer={isTrainer}
          isEnded={isEnded}
          traineeEvalsByReviewerId={traineeEvalsByReviewerId}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
        />
      </div>

      {/* Section 2: Bộ lọc & Bảng Học viên (Desktop) */}
      <div className="hidden md:block space-y-4">
        {meeting.enable_evaluation && (
          <EvaluationProgressFilterBar
            totalParticipants={totalParticipants}
            totalActiveTrainees={totalActiveTrainees}
            traineeEvaluatedCount={traineeEvaluatedCount}
            unratedCount={unratedCount}
            evalFilter={evalFilter}
            onFilterChange={setEvalFilter}
          />
        )}

        <TraineeListTable
          meeting={meeting}
          trainees={filteredTrainees}
          currentUserId={currentUserId}
          isTrainer={isTrainer}
          isEnded={isEnded}
          traineeEvalsByReviewerId={traineeEvalsByReviewerId}
          onOpenOverallEvaluation={onOpenOverallEvaluation}
          overallEval={overallEval}
          onViewEvaluation={handleViewEvaluation}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
        />
      </div>

      {/* Mobile: Danh sách phân chia 2 nhóm */}
      <div className="block md:hidden">
        <ParticipantMobileList
          meeting={meeting}
          trainers={trainerParticipants}
          trainees={filteredTrainees}
          currentUserId={currentUserId}
          isTrainer={isTrainer}
          isEnded={isEnded}
          traineeEvalsByReviewerId={traineeEvalsByReviewerId}
          onOpenOverallEvaluation={onOpenOverallEvaluation}
          overallEval={overallEval}
          onViewEvaluation={handleViewEvaluation}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
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

      <EvaluationDetailModal
        open={isEvaluationDetailModalOpen}
        evaluation={selectedEvaluation}
        onClose={() => {
          setIsEvaluationDetailModalOpen(false);
          setSelectedEvaluation(null);
        }}
      />
    </div>
  );
};
