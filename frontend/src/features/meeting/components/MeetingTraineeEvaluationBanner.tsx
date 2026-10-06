import React, { useState } from 'react';
import { Card, Typography, Space, Button } from 'antd';
import { StarOutlined, TrophyOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useMeetingDetail } from '../hooks/useMeetings';
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

  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);

  if (!meeting) return null;

  const currentUserId = user?.id;
  const myParticipantRecord = meeting.participants.find((p) => p.user_id === currentUserId);
  const isTrainee = !!myParticipantRecord;
  const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

  if (!meeting.enable_evaluation || !isTrainee || !isEnded) {
    return null;
  }

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <Card className="border-amber-200 bg-amber-50/50 shadow-sm" style={{ width: '100%' }}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <StarOutlined className="text-2xl text-amber-500 mt-1" />
              <div>
                <Text strong className="text-base text-amber-900 block">
                  Khu vực Đánh giá dành cho Học viên
                </Text>
                <Text type="secondary" className="text-xs text-amber-700">
                  Hãy gửi đánh giá cho Trainer để mở khóa xem điểm rèn luyện cá nhân và lời nhận xét mà Trainer dành cho bạn.
                </Text>
              </div>
            </div>
            <Space>
              <Button
                type="default"
                icon={<TrophyOutlined className="text-yellow-600" />}
                onClick={() => setIsMyResultOpen(true)}
              >
                Điểm của tôi
              </Button>
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
      </div>

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
