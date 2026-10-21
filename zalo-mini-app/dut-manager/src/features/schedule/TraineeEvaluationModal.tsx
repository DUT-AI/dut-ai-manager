import React, { useState } from 'react';
import { Modal, Button, useSnackbar } from 'zmp-ui';
import type { ParticipantResponse } from '@/types/meeting.types';
import { meetingService } from '@/services/api/meeting.service';

interface TraineeEvaluationModalProps {
  meetingId: number;
  trainee: ParticipantResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const TraineeEvaluationModal: React.FC<TraineeEvaluationModalProps> = ({
  meetingId,
  trainee,
  onClose,
  onSuccess,
}) => {
  const { openSnackbar } = useSnackbar();
  const [skillScore, setSkillScore] = useState<number>(8);
  const [attitudeScore, setAttitudeScore] = useState<number>(9);
  const [feedback, setFeedback] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!trainee) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await meetingService.submitTrainerEvaluation(meetingId, {
        target_user_id: trainee.user_id,
        scores: [
          { criteria_code: 'TECHNICAL_SKILL', score: skillScore },
          { criteria_code: 'ATTITUDE', score: attitudeScore },
        ],
        feedback_text: feedback,
      });

      if (res.is_success) {
        openSnackbar({ text: 'Đã lưu đánh giá học viên thành công', type: 'success' });
        onSuccess();
        onClose();
      } else {
        openSnackbar({ text: res.message || 'Lưu đánh giá thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Lỗi khi gửi đánh giá', type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal visible={!!trainee} title="Đánh giá học viên (Trainee)" onClose={onClose} maskClosable>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 py-2">
        <p className="text-xs text-gray-500">
          Học viên: <strong className="text-gray-900">{trainee.user_name || `#${trainee.user_id}`}</strong>
        </p>

        {/* Technical Skill Criteria */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-gray-700">Kỹ năng & Mức độ tiếp thu (1-10)</span>
            <span className="font-extrabold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">
              {skillScore}/10
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={skillScore}
            onChange={(e) => setSkillScore(Number(e.target.value))}
            className="w-full accent-blue-600"
          />
        </div>

        {/* Attitude Criteria */}
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-gray-700">Thái độ & Tương tác (1-10)</span>
            <span className="font-extrabold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
              {attitudeScore}/10
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={attitudeScore}
            onChange={(e) => setAttitudeScore(Number(e.target.value))}
            className="w-full accent-indigo-600"
          />
        </div>

        {/* Feedback Text */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-700">Nhận xét chi tiết</label>
          <textarea
            rows={3}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Nhận xét ưu điểm, điểm cần cải thiện của học viên..."
            className="w-full border border-gray-200 rounded-xl p-2.5 text-xs outline-none focus:border-blue-500 resize-none bg-white"
          />
        </div>

        <div className="flex gap-2 mt-3">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
            Hủy
          </Button>
          <Button
            htmlType="submit"
            loading={isSubmitting}
            className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
          >
            Lưu đánh giá
          </Button>
        </div>
      </form>
    </Modal>
  );
};
