import React, { useState } from 'react';
import { Typography, Button, Popconfirm, message } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ParticipantStatus } from '../types/meeting.types';
import { useMeetingDetail, useUpdateParticipantStatus } from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';

const { Text } = Typography;

interface Props {
  meetingId: number;
}

export const MeetingBatchCheckInBanner: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();
  const [isCheckingInAll, setIsCheckingInAll] = useState(false);
  const updateParticipantStatusMutation = useUpdateParticipantStatus();

  if (!meeting) return null;

  const currentUserId = user?.id;
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader'].includes(r.toLowerCase())) ?? false);

  const unjoinedParticipants = meeting.participants.filter(
    (p) => p.status === ParticipantStatus.NOT_JOINED && !p.check_in_at
  );
  const unjoinedCount = unjoinedParticipants.length;

  if (!isTrainer || unjoinedCount === 0) {
    return null;
  }

  const handleQuickCheckInAll = async () => {
    try {
      setIsCheckingInAll(true);
      const promises = unjoinedParticipants.map((p) =>
        updateParticipantStatusMutation.mutateAsync({
          meetingId: meeting.id,
          userId: p.user_id,
          payload: {
            status: ParticipantStatus.JOINED,
            check_in_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
          },
        })
      );
      await Promise.all(promises);
      message.success(`Đã điểm danh thành công cho ${unjoinedCount} học viên`);
      refetch();
    } catch {
      message.error('Có lỗi xảy ra khi điểm danh tất cả');
    } finally {
      setIsCheckingInAll(false);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-3.5 shadow-sm">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold">
          <ThunderboltOutlined />
        </div>
        <div>
          <Text strong className="text-emerald-950 text-sm block">
            Điểm danh nhanh hàng loạt
          </Text>
          <Text type="secondary" className="text-xs text-emerald-800">
            Hiện có <strong>{unjoinedCount}</strong> học viên chưa check-in buổi học này.
          </Text>
        </div>
      </div>
      <Popconfirm
        title="Điểm danh nhanh tất cả?"
        description={`Bạn có chắc muốn điểm danh nhanh cho tất cả ${unjoinedCount} học viên chưa check-in?`}
        onConfirm={handleQuickCheckInAll}
        okText="Điểm danh tất cả"
        cancelText="Hủy"
        disabled={isCheckingInAll}
      >
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          className="bg-emerald-600 hover:!bg-emerald-500 shadow-sm font-medium"
          loading={isCheckingInAll}
        >
          Điểm danh tất cả ({unjoinedCount})
        </Button>
      </Popconfirm>
    </div>
  );
};
