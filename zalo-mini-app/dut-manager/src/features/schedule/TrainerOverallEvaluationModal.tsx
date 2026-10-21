import React, { useState } from 'react';
import { Modal, Button, Icon, useSnackbar } from 'zmp-ui';
import { meetingService } from '@/services/api/meeting.service';
import type { MeetingOverallEvaluationResponse } from '@/types/meeting.types';

export const MEETING_OVERALL_CRITERIA = [
  {
    code: 'ATTENDANCE_CONDUCT',
    label: 'Chuyên cần & Tác phong',
    desc: 'Đúng giờ, tuân thủ nội quy và kỷ luật chung của lớp học',
  },
  {
    code: 'INTERACTION_CONTRIBUTION',
    label: 'Mức độ Tương tác & Đóng góp',
    desc: 'Tích cực phát biểu, đặt câu hỏi, thảo luận sôi nổi',
  },
  {
    code: 'ABSORPTION_COMPREHENSION',
    label: 'Mức độ Tiếp thu & Hiểu bài',
    desc: 'Mức độ nắm bắt kiến thức cốt lõi truyền đạt trong buổi học',
  },
  {
    code: 'PRE_CLASS_PREPARATION',
    label: 'Mức độ Chuẩn bị bài trước buổi học',
    desc: 'Đọc trước tài liệu, chuẩn bị bài tập / môi trường trước khi lên lớp',
  },
];

interface TrainerOverallEvaluationModalProps {
  isOpen: boolean;
  meetingId: number;
  meetingTitle?: string;
  existingEvaluation?: MeetingOverallEvaluationResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const TrainerOverallEvaluationModal: React.FC<TrainerOverallEvaluationModalProps> = ({
  isOpen,
  meetingId,
  meetingTitle,
  existingEvaluation,
  onClose,
  onSuccess,
}) => {
  const { openSnackbar } = useSnackbar();

  // Khởi tạo điểm cho 4 tiêu chí chuẩn của Web (thang điểm 1 - 5)
  const [scores, setScores] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    MEETING_OVERALL_CRITERIA.forEach((c) => {
      const found = existingEvaluation?.scores?.find((s) => s.criteria_code === c.code);
      initial[c.code] = found ? found.score : 5;
    });
    return initial;
  });

  const [generalFeedback, setGeneralFeedback] = useState<string>(
    existingEvaluation?.general_feedback || ''
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const setCriteriaScore = (code: string, val: number) => {
    setScores((prev) => ({ ...prev, [code]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payloadScores = MEETING_OVERALL_CRITERIA.map((c) => ({
        criteria_code: c.code,
        score: scores[c.code] || 5,
      }));

      const res = await meetingService.submitMeetingOverallEvaluation(meetingId, {
        scores: payloadScores,
        general_feedback: generalFeedback.trim() || undefined,
      });

      if (res.is_success) {
        openSnackbar({
          text: existingEvaluation
            ? 'Cập nhật đánh giá lớp học thành công!'
            : 'Đã hoàn thành đánh giá buổi học!',
          type: 'success',
        });
        onSuccess();
        onClose();
      } else {
        openSnackbar({ text: res.message || 'Lưu đánh giá thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Có lỗi khi gửi đánh giá', type: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal visible={isOpen} title="Trainer Đánh giá Lớp học" onClose={onClose} maskClosable>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 py-2">
        {meetingTitle && (
          <div className="bg-blue-50/70 p-2.5 rounded-xl border border-blue-100">
            <span className="text-[11px] font-medium text-gray-500">Buổi học:</span>
            <p className="text-xs font-bold text-blue-900 truncate">{meetingTitle}</p>
          </div>
        )}

        <p className="text-xs text-gray-600 font-medium">
          Vui lòng đánh giá các tiêu chí chung của lớp theo thang điểm từ 1 đến 5 sao:
        </p>

        {/* 4 Tiêu chí chuẩn như Web */}
        <div className="flex flex-col gap-3">
          {MEETING_OVERALL_CRITERIA.map((c) => {
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

                {/* 5 Star selector */}
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

        {/* Nhận xét chung */}
        <div className="flex flex-col gap-1 mt-1">
          <label className="text-xs font-bold text-gray-700">Nhận xét chung buổi học</label>
          <textarea
            rows={3}
            value={generalFeedback}
            onChange={(e) => setGeneralFeedback(e.target.value)}
            placeholder="Nội dung lớp học đã đạt được, tinh thần học tập chung..."
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
            {existingEvaluation ? 'Cập nhật' : 'Hoàn tất đánh giá'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
