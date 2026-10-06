import React, { useState } from 'react';
import { Table, Avatar, Tag, Typography, Image, Button } from 'antd';
import { UserOutlined, StarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ParticipantResponse, UpdateParticipantStatusPayload } from '../types/meeting.types';
import { useMeetingDetail, useUpdateParticipantStatus } from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { ParticipantStatusTag } from './ParticipantStatusTag';
import { ParticipantActionButtons } from './ParticipantActionButtons';
import { MeetingBatchCheckInBanner } from './MeetingBatchCheckInBanner';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';
import { TrainerEvaluationModal } from './TrainerEvaluationModal';

const { Text } = Typography;

interface Props {
  meetingId: number;
}

export const MeetingParticipantsTab: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();

  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [isEditStatusModalOpen, setIsEditStatusModalOpen] = useState(false);
  const [evaluatingParticipant, setEvaluatingParticipant] = useState<ParticipantResponse | null>(null);

  const updateParticipantStatusMutation = useUpdateParticipantStatus();

  if (!meeting) return null;

  const currentUserId = user?.id;
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (meeting.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);

  const isEnded = dayjs().isAfter(dayjs(meeting.end_time));
  const totalParticipants = meeting.participants.length;

  const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
    if (!editingParticipant) return;
    await updateParticipantStatusMutation.mutateAsync({
      meetingId: meeting.id,
      userId: editingParticipant.user_id,
      payload,
    });
    refetch();
  };

  const columns = [
    {
      title: 'Thành viên',
      key: 'user',
      render: (_: unknown, record: ParticipantResponse) => (
        <div className="flex items-center gap-3">
          <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="default" />
          <div>
            <Text strong className="block text-sm">
              {record.user_name || `User #${record.user_id}`}
            </Text>
            {record.user_id === meeting.created_by && (
              <Tag color="gold" className="text-[10px] m-0">
                Trainer / Tạo buổi
              </Tag>
            )}
          </div>
        </div>
      ),
      sorter: (a: ParticipantResponse, b: ParticipantResponse) =>
        (a.user_name || '').localeCompare(b.user_name || ''),
    },
    {
      title: 'Trạng thái tham gia',
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => <ParticipantStatusTag status={status} />,
      sorter: (a: ParticipantResponse, b: ParticipantResponse) =>
        (a.status || '').localeCompare(b.status || ''),
    },
    {
      title: 'Check-in',
      dataIndex: 'check_in_at',
      key: 'check_in_at',
      render: (text: string) => (text ? dayjs(text).format('HH:mm:ss') : '—'),
      sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
        if (!a.check_in_at) return 1;
        if (!b.check_in_at) return -1;
        return dayjs(a.check_in_at).unix() - dayjs(b.check_in_at).unix();
      },
    },
    {
      title: 'Check-out',
      dataIndex: 'check_out_at',
      key: 'check_out_at',
      render: (text: string, record: ParticipantResponse) => {
        if (text) return dayjs(text).format('HH:mm:ss');
        if (isEnded && record.check_in_at) {
          return `${dayjs(meeting.end_time).format('HH:mm')} (Tự động)`;
        }
        return '—';
      },
      sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
        const aTime = a.check_out_at || (isEnded && a.check_in_at ? meeting.end_time : null);
        const bTime = b.check_out_at || (isEnded && b.check_in_at ? meeting.end_time : null);
        if (!aTime) return 1;
        if (!bTime) return -1;
        return dayjs(aTime).unix() - dayjs(bTime).unix();
      },
    },
    {
      title: 'Ảnh quẹt thẻ / Checkin',
      dataIndex: 'link_image',
      key: 'link_image',
      render: (url: string) =>
        url ? (
          <Image
            src={url}
            alt="Checkin"
            width={44}
            height={44}
            className="rounded-lg object-cover cursor-pointer hover:opacity-85 shadow-sm border border-gray-100"
            preview={{
              mask: <div className="text-[11px]">Xem ảnh</div>,
            }}
          />
        ) : (
          <Text type="secondary" className="text-xs">
            —
          </Text>
        ),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_: unknown, record: ParticipantResponse) => (
        <ParticipantActionButtons
          meetingId={meetingId}
          record={record}
          isTrainer={isTrainer}
          isEnded={isEnded}
          enableEvaluation={meeting.enable_evaluation}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
          onEvaluate={(p) => setEvaluatingParticipant(p)}
        />
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Batch Check-in Banner if unjoined participants exist */}
      <MeetingBatchCheckInBanner meetingId={meetingId} />


      {/* Participants Table */}
      <Table
        dataSource={meeting.participants}
        columns={columns}
        rowKey="user_id"
        pagination={totalParticipants > 10 ? { pageSize: 10 } : false}
        className="mt-2"
      />

      {/* Edit Attendance Status Modal */}
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

      {/* Trainer Evaluation Modal */}
      {evaluatingParticipant && (
        <TrainerEvaluationModal
          open={!!evaluatingParticipant}
          meetingId={meeting.id}
          trainee={evaluatingParticipant}
          participants={meeting.participants}
          onSelectTrainee={(p) => setEvaluatingParticipant(p)}
          onSuccess={() => {
            setEvaluatingParticipant(null);
            refetch();
          }}
          onClose={() => setEvaluatingParticipant(null)}
          onCancel={() => setEvaluatingParticipant(null)}
        />
      )}
    </div>
  );
};
