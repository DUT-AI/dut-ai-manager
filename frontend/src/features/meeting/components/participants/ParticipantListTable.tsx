import React from 'react';
import { Table, Avatar, Tag, Typography, Image } from 'antd';
import { UserOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import type { ParticipantResponse, EvaluationResponse, MeetingResponse, MeetingDetailResponse } from '../../types/meeting.types';
import { ParticipantStatusTag } from '../ParticipantStatusTag';
import { ParticipantActionButtons } from '../ParticipantActionButtons';

const { Text } = Typography;

interface Props {
  meeting: MeetingResponse | MeetingDetailResponse;
  participants: ParticipantResponse[];
  currentUserId?: number;
  isTrainer: boolean;
  isEnded: boolean;
  trainerEvalsByTraineeId: Map<number, EvaluationResponse>;
  traineeEvalsByReviewerId: Map<number, EvaluationResponse>;
  onEditStatus: (participant: ParticipantResponse) => void;
  onEvaluate: (participant: ParticipantResponse) => void;
}

export const ParticipantListTable: React.FC<Props> = ({
  meeting,
  participants,
  currentUserId,
  isTrainer,
  isEnded,
  trainerEvalsByTraineeId,
  traineeEvalsByReviewerId,
  onEditStatus,
  onEvaluate,
}) => {
  const columns: ColumnsType<ParticipantResponse> = [
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
    ...(meeting.enable_evaluation
      ? [
          {
            title: 'Đánh giá Trainer',
            key: 'trainee_eval',
            render: (_: unknown, record: ParticipantResponse) => {
              if (record.user_id === meeting.created_by) {
                return <Text type="secondary" className="text-xs">—</Text>;
              }
              const existing = traineeEvalsByReviewerId.get(record.user_id);
              if (existing) {
                const isAnonymous = existing.is_anonymous;
                return (
                  <Tag
                    color={isAnonymous ? 'purple' : 'blue'}
                    icon={<CheckCircleOutlined />}
                    className="text-xs py-0.5 px-2"
                  >
                    {isAnonymous ? 'Đã gửi (Ẩn danh)' : 'Đã gửi'}
                    {record.user_id === currentUserId
                      ? ` (⭐ ${existing.average_score.toFixed(1)})`
                      : ''}
                  </Tag>
                );
              }
              return <Tag color="default" className="text-xs py-0.5 px-2">Chưa gửi</Tag>;
            },
          },
        ]
      : []),
    {
      title: 'Ảnh quẹt thẻ',
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
          meetingId={meeting.id}
          record={record}
          isTrainer={isTrainer}
          isEnded={isEnded}
          enableEvaluation={meeting.enable_evaluation}
          existingEvaluation={trainerEvalsByTraineeId.get(record.user_id)}
          onEditStatus={onEditStatus}
          onEvaluate={onEvaluate}
        />
      ),
    },
  ];

  return (
    <Table
      dataSource={participants}
      columns={columns}
      rowKey="user_id"
      pagination={participants.length > 10 ? { pageSize: 10 } : false}
      scroll={{ x: 800 }}
      className="mt-2 shadow-sm rounded-lg overflow-hidden border border-gray-100"
    />
  );
};
