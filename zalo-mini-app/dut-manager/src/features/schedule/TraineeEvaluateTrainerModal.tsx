import React, { useState } from 'react';
import { Modal, Button, Icon, useSnackbar, Avatar } from 'zmp-ui';
import { meetingService } from '@/services/api/meeting.service';
import type { EvaluationResponse } from '@/types/meeting.types';

export const TRAINEE_TO_TRAINER_CRITERIA = [
  {
    code: 'CONTENT_QUALITY',
    label: 'Chất lượng Nội dung bài học',
    desc: 'Rõ ràng, thực tế, bố cục bài giảng hợp lý và dễ theo dõi',
  },
  {
    code: 'TEACHING_METHOD',
    label: 'Phương pháp Giảng dạy & Hỗ trợ',
    desc: 'Trainer truyền đạt dễ hiểu, nhiệt tình giải đáp các thắc mắc',
  },
  {
    code: 'CLASS_ATMOSPHERE',
    label: 'Không khí Lớp học & Sự tương tác',
    desc: 'Lôi cuốn, truyền cảm hứng và tạo động lực học tập tốt',
  },
  {
    code: 'PRACTICAL_VALUE',
    label: 'Giá trị Thu nhận & Tính ứng dụng',
    desc: 'Kiến thức thu nhận bổ ích, có thể ứng dụng trực tiếp vào thực tế',
  },
];

interface TraineeEvaluateTrainerModalProps {
  isOpen: boolean;
  meetingId: number;
  trainerId?: number;
  trainerName?: string;
  trainerAvatarUrl?: string | null;
  existingEvaluation?: EvaluationResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const TraineeEvaluateTrainerModal: React.FC<TraineeEvaluateTrainerModalProps> = ({
  isOpen,
  meetingId,
  trainerId,
  trainerName,
  trainerAvatarUrl,
  existingEvaluation,
  onClose,
  onSuccess,
}) => {
  const { openSnackbar } = useSnackbar();

  // Khởi tạo điểm cho 4 tiêu chí chuẩn của Web (1 - 5 sao)
  const [scores, setScores] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    TRAINEE_TO_TRAINER_CRITERIA.forEach((c) => {
      const found = existingEvaluation?.scores?.find((s) => s.criteria_code === c.code);
      initial[c.code] = found ? found.score : 5;
    });
    return initial;
  });

  const [isAnonymous, setIsAnonymous] = useState<boolean>(
    existingEvaluation?.is_anonymous ?? false
  );
  const [feedbackText, setFeedbackText] = useState<string>(
    existingEvaluation?.feedback_text || ''
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const setCriteriaScore = (code: string, val: number) => {
    setScores((prev) => ({ ...prev, [code]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payloadScores = TRAINEE_TO_TRAINER_CRITERIA.map((c) => ({
        criteria_code: c.code,
        score: scores[c.code] || 5,
      }));

      const payload: any = {
        is_anonymous: isAnonymous,
        scores: payloadScores,
        feedback_text: feedbackText.trim() || undefined,
      };

      if (trainerId) {
        payload.target_user_id = trainerId;
      }

      const res = await meetingService.submitTraineeEvaluation(meetingId, payload);

      if (res.is_success) {
        openSnackbar({
          text: existingEvaluation
            ? 'Đã cập nhật đánh giá cho Trainer!'
            : 'Đã gửi đánh giá cho Trainer thành công!',
          type: 'success',
        });
        onSuccess();
        onClose();
      } else {
        openSnackbar({ text: res.message || 'Gửi đánh giá thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Có lỗi khi gửi đánh giá', type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal visible={isOpen} title="Đánh giá Trainer" onClose={onClose} maskClosable>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 py-2">
        {/* Trainer Info Card */}
        <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100">
          <Avatar
            src={trainerAvatarUrl || undefined}
            size={40}
            className="shrink-0 bg-blue-600 text-white font-bold"
          >
            {trainerName?.charAt(0)?.toUpperCase() || 'T'}
          </Avatar>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-bold text-gray-900 truncate">
              {trainerName || 'Giảng viên / Trainer'}
            </span>
            <span className="text-[10px] text-gray-500">Người phụ trách buổi sinh hoạt</span>
          </div>
        </div>

        {/* Anonymous Toggle */}
        <div className="flex items-center justify-between p-2.5 rounded-xl bg-gray-50 border border-gray-100">
          <div className="flex items-center gap-2">
            <Icon
              icon={isAnonymous ? 'zi-radio-checked' : 'zi-radio-unchecked'}
              size={18}
              className={isAnonymous ? 'text-blue-600' : 'text-gray-500'}
            />
            <span className="text-xs font-semibold text-gray-700">Đánh giá ẩn danh</span>
          </div>
          <button
            type="button"
            onClick={() => setIsAnonymous((prev) => !prev)}
            className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors ${
              isAnonymous ? 'bg-blue-600 justify-end' : 'bg-gray-300 justify-start'
            }`}
          >
            <div className="w-4 h-4 rounded-full bg-white shadow-xs"></div>
          </button>
        </div>

        <p className="text-xs text-gray-600 font-medium">
          Đánh giá mức độ hài lòng về chất lượng giảng dạy (1 - 5 sao):
        </p>

        {/* 4 Tiêu chí chuẩn như Web */}
        <div className="flex flex-col gap-2.5">
          {TRAINEE_TO_TRAINER_CRITERIA.map((c) => {
            const currentScore = scores[c.code] || 5;
            return (
              <div key={c.code} className="bg-gray-50/80 p-3 rounded-2xl border border-gray-100 flex flex-col gap-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-xs font-bold text-gray-900">{c.label}</h4>
                    <p className="text-[11px] text-gray-500 leading-snug">{c.desc}</p>
                  </div>
                  <span className="text-xs font-extrabold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md shrink-0">
                    {currentScore}/5 ★
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      type="button"
                      key={star}
                      onClick={() => setCriteriaScore(c.code, star)}
                      className="p-1 transition-transform active:scale-90"
                    >
                      <Icon
                        icon="zi-star-solid"
                        size={22}
                        className={star <= currentScore ? 'text-amber-400' : 'text-gray-300'}
                      />
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Nhận xét / Góp ý */}
        <div className="flex flex-col gap-1 mt-1">
          <label className="text-xs font-bold text-gray-700">Góp ý cho Trainer (tùy chọn)</label>
          <textarea
            rows={3}
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Chia sẻ cảm nhận hoặc góp ý giúp Trainer nâng cao chất lượng..."
            className="w-full border border-gray-200 rounded-xl p-2.5 text-xs outline-none focus:border-blue-500 resize-none bg-white"
          />
        </div>

        <div className="flex gap-2 mt-2 sticky bottom-0 bg-white pt-2 border-t border-gray-100">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
            Hủy
          </Button>
          <Button
            htmlType="submit"
            loading={isSubmitting}
            className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
          >
            {existingEvaluation ? 'Cập nhật' : 'Gửi đánh giá'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
