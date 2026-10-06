import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Tag, Button, Popconfirm, message, Space } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  SafetyCertificateOutlined,
  EditOutlined,
  DeleteOutlined,
  StarOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useMeetingDetail, useDeleteMeeting, useUpdateMeeting } from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useUsers } from '@/features/users/hooks/useUsers';
import { MeetingModal } from './MeetingModal';
import { TraineeEvaluationModal } from './TraineeEvaluationModal';
import { MyEvaluationResultModal } from './MyEvaluationResultModal';

const { Title, Paragraph } = Typography;

interface Props {
  meetingId: number;
}

export const MeetingHeroHeader: React.FC<Props> = ({ meetingId }) => {
  const navigate = useNavigate();
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();
  const { data: users = [] } = useUsers();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);
  const [isEnabling, setIsEnabling] = useState(false);

  const deleteMeetingMutation = useDeleteMeeting();
  const updateMeetingMutation = useUpdateMeeting();

  if (!meeting) return null;

  const currentUserId = user?.id;
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (meeting.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);

  const myParticipantRecord = meeting.participants.find((p) => p.user_id === currentUserId);
  const isTrainee = !!myParticipantRecord;

  const isOngoing = dayjs().isAfter(dayjs(meeting.start_time)) && dayjs().isBefore(dayjs(meeting.end_time));
  const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

  const handleDeleteMeeting = async () => {
    try {
      await deleteMeetingMutation.mutateAsync(meeting.id);
      message.success('Đã xóa buổi học thành công');
      navigate('/dashboard/meetings');
    } catch {
      message.error('Không thể xóa buổi học');
    }
  };

  const handleEditSubmit = async (data: any) => {
    try {
      await updateMeetingMutation.mutateAsync({ id: meeting.id, data });
      message.success('Cập nhật buổi học thành công');
      setIsEditModalOpen(false);
      refetch();
    } catch {
      message.error('Không thể cập nhật buổi học');
    }
  };

  const handleQuickEnableEvaluation = async () => {
    try {
      setIsEnabling(true);
      await updateMeetingMutation.mutateAsync({
        id: meeting.id,
        data: { enable_evaluation: true },
      });
      message.success('Đã kích hoạt tính năng Đánh giá 2 chiều');
      refetch();
    } catch {
      message.error('Không thể kích hoạt đánh giá');
    } finally {
      setIsEnabling(false);
    }
  };

  return (
    <>
      <div
        className="rounded-2xl p-6 text-white shadow-lg relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        }}
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Title level={3} className="!text-white !mb-0">
                {meeting.title}
              </Title>
              {isOngoing && (
                <Tag color="processing" className="!bg-emerald-500/20 !text-emerald-200 border-none">
                  Đang diễn ra
                </Tag>
              )}
              {isEnded && (
                <Tag color="default" className="!bg-white/20 !text-white border-none">
                  Đã kết thúc
                </Tag>
              )}
              {meeting.enable_evaluation ? (
                <Tag color="warning" className="!bg-amber-500/20 !text-amber-200 border-none">
                  Đánh giá 2 chiều (Hạn 24h)
                </Tag>
              ) : (
                <Tag className="!bg-white/10 !text-white/70 border-none">
                  Đánh giá: Tắt
                </Tag>
              )}
            </div>

            <div className="flex items-center gap-4 text-white/80 text-sm flex-wrap">
              <span className="flex items-center gap-1.5">
                <CalendarOutlined />
                {dayjs(meeting.start_time).format('dddd, DD/MM/YYYY')}
              </span>
              <span className="flex items-center gap-1.5">
                <ClockCircleOutlined />
                {dayjs(meeting.start_time).format('HH:mm')} - {dayjs(meeting.end_time).format('HH:mm')}
              </span>
              {meeting.require_check_in && (
                <span className="flex items-center gap-1.5 text-emerald-200">
                  <SafetyCertificateOutlined />
                  Bắt buộc check-in
                </span>
              )}
            </div>

            {meeting.content && (
              <Paragraph className="!text-white/90 !mb-0 text-sm pt-2 max-w-3xl">
                {meeting.content}
              </Paragraph>
            )}
          </div>

          {/* Action buttons on header */}
          <div className="flex items-center gap-2 self-start md:self-center shrink-0 flex-wrap">
            {/* Quick Enable Evaluation Button */}
            {!meeting.enable_evaluation && isTrainer && (
              <Button
                ghost
                icon={<ThunderboltOutlined />}
                loading={isEnabling}
                onClick={handleQuickEnableEvaluation}
                className="!text-amber-200 !border-amber-300/60 hover:!bg-amber-500/20"
              >
                Bật Đánh giá 2 chiều
              </Button>
            )}

            {/* Trainee Evaluation Actions */}
            {meeting.enable_evaluation && (
              <>
                {isTrainee && (
                  <Button
                    ghost
                    icon={<TrophyOutlined />}
                    onClick={() => setIsMyResultOpen(true)}
                    className="!text-yellow-200 !border-yellow-300/60 hover:!bg-yellow-500/20"
                  >
                    Điểm của tôi
                  </Button>
                )}
                <Button
                  type="primary"
                  icon={<StarOutlined />}
                  onClick={() => setIsTraineeEvalOpen(true)}
                  className="bg-amber-500 hover:!bg-amber-400 !text-white border-none font-medium shadow-sm"
                >
                  Đánh giá Trainer
                </Button>
              </>
            )}

            {/* Trainer Edit/Delete Actions */}
            {isTrainer && (
              <Space size="small">
                <Button ghost icon={<EditOutlined />} onClick={() => setIsEditModalOpen(true)}>
                  Chỉnh sửa
                </Button>
                <Popconfirm
                  title="Xác nhận xóa buổi học?"
                  description="Bạn có chắc chắn muốn xóa buổi học này không?"
                  onConfirm={handleDeleteMeeting}
                  okText="Xóa"
                  cancelText="Hủy"
                >
                  <Button danger type="primary" icon={<DeleteOutlined />}>
                    Xóa
                  </Button>
                </Popconfirm>
              </Space>
            )}
          </div>
        </div>
      </div>

      <MeetingModal
        open={isEditModalOpen}
        editingItem={meeting}
        users={users}
        onSubmit={handleEditSubmit}
        onCancel={() => setIsEditModalOpen(false)}
      />

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

