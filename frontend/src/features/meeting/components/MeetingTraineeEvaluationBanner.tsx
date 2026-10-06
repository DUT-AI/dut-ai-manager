import React, { useState } from 'react';
import { Card, Typography, Space, Button, Alert, message } from 'antd';
import { StarOutlined, TrophyOutlined, ThunderboltOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useMeetingDetail, useUpdateMeeting } from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { TraineeEvaluationModal } from './TraineeEvaluationModal';
import { MyEvaluationResultModal } from './MyEvaluationResultModal';

const { Text } = Typography;

interface Props {
  meetingId: number;
}

export const MeetingTraineeEvaluationBanner: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();
  const updateMeetingMutation = useUpdateMeeting();

  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);
  const [isEnabling, setIsEnabling] = useState(false);

  if (!meeting) return null;

  const currentUserId = user?.id;
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (meeting.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);

  const myParticipantRecord = meeting.participants.find((p) => p.user_id === currentUserId);
  const isTrainee = !!myParticipantRecord;

  const handleQuickEnableEvaluation = async () => {
    try {
      setIsEnabling(true);
      await updateMeetingMutation.mutateAsync({
        id: meeting.id,
        data: { enable_evaluation: true },
      });
      message.success('Đã kích hoạt tính năng Đánh giá 2 chiều cho buổi học');
      refetch();
    } catch {
      message.error('Không thể kích hoạt đánh giá');
    } finally {
      setIsEnabling(false);
    }
  };

  // Case 1: Evaluation is DISABLED
  if (!meeting.enable_evaluation) {
    if (isTrainer) {
      return (
        <Alert
          type="info"
          showIcon
          icon={<InfoCircleOutlined className="text-indigo-500 text-lg" />}
          className="border-indigo-100 bg-indigo-50/70 rounded-xl"
          message={
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <Text strong className="text-indigo-950 block">
                  Tính năng Đánh giá 2 chiều (Trainer & Trainee) đang TẮT
                </Text>
                <Text type="secondary" className="text-xs text-indigo-700">
                  Bật tính năng này để Trainer có thể chấm điểm học viên và Học viên có thể gửi nhận xét, đánh giá cho Trainer.
                </Text>
              </div>
              <Button
                type="primary"
                size="small"
                icon={<ThunderboltOutlined />}
                loading={isEnabling}
                onClick={handleQuickEnableEvaluation}
                className="bg-indigo-600 hover:!bg-indigo-500 shrink-0"
              >
                Bật Đánh giá ngay
              </Button>
            </div>
          }
        />
      );
    }
    return null;
  }

  // Case 2: Evaluation is ENABLED
  // Shown for Trainees or Admins/Trainers exploring
  return (
    <>
      <Card className="border-amber-200 bg-amber-50/60 shadow-sm rounded-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <StarOutlined className="text-2xl text-amber-500 mt-1 shrink-0" />
            <div>
              <Text strong className="text-base text-amber-900 block">
                Khu vực Đánh giá Buổi học & Giảng viên
              </Text>
              <Text type="secondary" className="text-xs text-amber-800">
                {isTrainee
                  ? 'Gửi đánh giá cho Trainer để mở khóa xem điểm rèn luyện cá nhân và nhận xét chi tiết mà Trainer dành cho bạn.'
                  : 'Buổi học đã kích hoạt cơ chế đánh giá 2 chiều (Trainer đánh giá Học viên & Học viên đánh giá Trainer).'}
              </Text>
            </div>
          </div>
          <Space wrap className="shrink-0">
            {isTrainee && (
              <Button
                type="default"
                icon={<TrophyOutlined className="text-yellow-600" />}
                onClick={() => setIsMyResultOpen(true)}
              >
                Điểm của tôi
              </Button>
            )}
            <Button
              type="primary"
              className="bg-amber-600 hover:!bg-amber-500"
              icon={<StarOutlined />}
              onClick={() => setIsTraineeEvalOpen(true)}
            >
              Đánh giá Trainer
            </Button>
          </Space>
        </div>
      </Card>

      <TraineeEvaluationModal
        open={isTraineeEvalOpen}
        meetingId={meeting.id}
        trainerId={meeting.trainer?.id || meeting.created_by || undefined}
        trainerName={meeting.trainer?.name}
        trainerAvatarUrl={meeting.trainer?.avatar_url}
        onSuccess={() => {
          setIsTraineeEvalOpen(false);
          refetch();
        }}
        onClose={() => setIsTraineeEvalOpen(false)}
        onCancel={() => setIsTraineeEvalOpen(false)}
      />

      <MyEvaluationResultModal
        open={isMyResultOpen}
        meetingId={meeting.id}
        onClose={() => setIsMyResultOpen(false)}
      />
    </>
  );
};

