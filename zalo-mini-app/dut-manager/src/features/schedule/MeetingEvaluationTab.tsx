import React, { useState } from 'react';
import { Button, Icon } from 'zmp-ui';
import type {
  MeetingDetailResponse,
  MeetingEvaluationSummary,
  MeetingOverallEvaluationResponse,
  EvaluationResponse,
} from '@/types/meeting.types';
import { TrainerOverallEvaluationModal } from './TrainerOverallEvaluationModal';
import { TraineeEvaluateTrainerModal } from './TraineeEvaluateTrainerModal';

interface MeetingEvaluationTabProps {
  meeting: MeetingDetailResponse;
  currentUserId?: number;
  isTrainer: boolean;
  hasUpdatePermission: boolean;
  overallEvaluation?: MeetingOverallEvaluationResponse | null;
  myEvalForTrainer?: EvaluationResponse | null;
  evaluationSummary?: MeetingEvaluationSummary | null;
  onRefetch: () => void;
}

export const MeetingEvaluationTab: React.FC<MeetingEvaluationTabProps> = ({
  meeting,
  currentUserId,
  isTrainer,
  hasUpdatePermission,
  overallEvaluation,
  myEvalForTrainer,
  evaluationSummary,
  onRefetch,
}) => {
  const [isTrainerModalOpen, setIsTrainerModalOpen] = useState(false);
  const [isTraineeModalOpen, setIsTraineeModalOpen] = useState(false);

  const canEvaluateClass = isTrainer || hasUpdatePermission;
  const trainer = meeting.trainer;

  return (
    <div className="flex flex-col gap-3">
      {/* 1. Trainee Evaluation Action Banner */}
      <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-500 flex items-center justify-center font-bold shrink-0">
              <Icon icon="zi-star-solid" size={20} />
            </div>
            <div className="flex flex-col min-w-0">
              <h3 className="text-xs font-bold text-gray-900 truncate">Đánh giá Trainer</h3>
              <p className="text-[11px] text-gray-500 truncate">
                {trainer ? `Người phụ trách: ${trainer.name}` : 'Dành cho học viên trong lớp'}
              </p>
            </div>
          </div>

          <Button
            size="small"
            onClick={() => setIsTraineeModalOpen(true)}
            className={`rounded-xl text-xs font-bold px-3 py-1.5 shrink-0 whitespace-nowrap shadow-xs ${
              myEvalForTrainer
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-blue-600 text-white'
            }`}
          >
            {myEvalForTrainer ? '✓ Đã gửi' : 'Đánh giá ngay'}
          </Button>
        </div>

        {myEvalForTrainer && (
          <div className="bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-100 text-[11px] text-emerald-900 flex items-center justify-between">
            <span>
              Điểm đánh giá của bạn:{' '}
              <strong className="text-emerald-700 font-bold">
                {myEvalForTrainer.average_score}/5 ★
              </strong>
              {myEvalForTrainer.is_anonymous && ' (Ẩn danh)'}
            </span>
            <button
              onClick={() => setIsTraineeModalOpen(true)}
              className="text-emerald-700 font-bold underline"
            >
              Chỉnh sửa
            </button>
          </div>
        )}
      </div>

      {/* 2. Trainer Class Evaluation Card */}
      {canEvaluateClass && (
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold shrink-0">
                <Icon icon="zi-check-circle" size={20} />
              </div>
              <div className="flex flex-col min-w-0">
                <h3 className="text-xs font-bold text-gray-900 truncate">Đánh giá Lớp học</h3>
                <p className="text-[11px] text-gray-500 line-clamp-1">
                  Dành cho Trainer tổng kết buổi học
                </p>
              </div>
            </div>

            <Button
              size="small"
              onClick={() => setIsTrainerModalOpen(true)}
              className={`rounded-xl text-xs font-bold px-3 py-1.5 shrink-0 whitespace-nowrap shadow-xs ${
                overallEvaluation
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-blue-600 text-white'
              }`}
            >
              {overallEvaluation ? '✓ Đã xong' : 'Đánh giá lớp'}
            </Button>
          </div>

          {overallEvaluation && (
            <div className="bg-blue-50/40 p-3 rounded-xl border border-blue-100 flex flex-col gap-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-700">Điểm đánh giá chung của Trainer:</span>
                <span className="font-extrabold text-blue-700 bg-white px-2 py-0.5 rounded-md shadow-xs">
                  {overallEvaluation.average_score}/5 ★
                </span>
              </div>
              {overallEvaluation.general_feedback && (
                <p className="text-[11px] text-gray-600 italic bg-white/70 p-2 rounded-lg">
                  "{overallEvaluation.general_feedback}"
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* 3. Summary Criteria Breakdown (if available) */}
      {evaluationSummary && evaluationSummary.criteria_breakdown?.length > 0 && (
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-gray-900">Chi tiết tiêu chí đánh giá</h3>
            <span className="text-[11px] text-gray-500">
              {evaluationSummary.total_evaluations} lượt đánh giá
            </span>
          </div>

          <div className="flex flex-col gap-2 pt-1">
            {evaluationSummary.criteria_breakdown.map((item) => (
              <div
                key={item.criteria_code}
                className="flex items-center justify-between p-2 rounded-xl bg-gray-50 text-xs"
              >
                <div className="flex flex-col min-w-0 pr-2">
                  <span className="font-semibold text-gray-800 truncate">{item.criteria_name}</span>
                  <span className="text-[10px] text-gray-400">{item.count} lượt</span>
                </div>
                <span className="font-extrabold text-amber-600 shrink-0">
                  {item.average_score.toFixed(1)}/5 ★
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal Trainer Đánh giá Lớp */}
      <TrainerOverallEvaluationModal
        isOpen={isTrainerModalOpen}
        meetingId={meeting.id}
        meetingTitle={meeting.title}
        existingEvaluation={overallEvaluation}
        onClose={() => setIsTrainerModalOpen(false)}
        onSuccess={onRefetch}
      />

      {/* Modal Trainee Đánh giá Trainer */}
      <TraineeEvaluateTrainerModal
        isOpen={isTraineeModalOpen}
        meetingId={meeting.id}
        trainerId={trainer?.id}
        trainerName={trainer?.name}
        trainerAvatarUrl={trainer?.avatar_url}
        existingEvaluation={myEvalForTrainer}
        onClose={() => setIsTraineeModalOpen(false)}
        onSuccess={onRefetch}
      />
    </div>
  );
};
