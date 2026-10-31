import React from 'react';
import { Table, Avatar, Tag, Typography, Image, Button, Tooltip, Empty, Space } from 'antd';
import { UserOutlined, CrownOutlined, EditOutlined, StarFilled } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import type { ParticipantResponse, MeetingResponse, MeetingDetailResponse, EvaluationResponse } from '../../types/meeting.types';
import { ParticipantStatusTag } from '../ParticipantStatusTag';

const { Text } = Typography;

interface Props {
  meeting: MeetingResponse | MeetingDetailResponse;
  trainers: ParticipantResponse[];
  currentUserId?: number;
  isTrainer: boolean;
  isEnded: boolean;
  traineeEvalsByReviewerId?: Map<number, EvaluationResponse>;
  onEditStatus: (participant: ParticipantResponse) => void;
}

export const TrainerListTable: React.FC<Props> = ({
  meeting,
  trainers,
  isTrainer,
  isEnded,
  onEditStatus,
}) => {
  const columns: ColumnsType<ParticipantResponse> = [
    {
      title: 'Giảng viên / Người phụ trách',
      key: 'user',
      render: (_: unknown, record: ParticipantResponse) => (
        <div className="flex items-center gap-3">
          <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="default" className="border border-amber-300" />
          <div>
            <div className="flex items-center gap-1.5">
              <Text strong className="text-sm">
                {record.user_name || `User #${record.user_id}`}
              </Text>
              <Tag color="gold" className="text-[10px] m-0 font-medium border-amber-300">
                <CrownOutlined className="text-amber-600 mr-0.5" /> Trainer
              </Tag>
            </div>
            {record.user_id === meeting.created_by && (
              <span className="text-[11px] text-gray-400 block">
                Người khởi tạo meeting
              </span>
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
    },
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
        <Space size="small">
          {isTrainer && (
            <Tooltip title="Chỉnh sửa trạng thái điểm danh">
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={() => onEditStatus(record)}
              >
                Sửa trạng thái
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  if (trainers.length === 0) {
    return (
      <div className="bg-amber-50/40 p-4 rounded-xl border border-dashed border-amber-200 text-center">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div className="text-xs text-amber-800">
              Buổi sinh hoạt tự quản / tự học nhóm (không có Trainer phụ trách)
            </div>
          }
        />
      </div>
    );
  }

  return (
    <Table
      dataSource={trainers}
      columns={columns}
      rowKey="user_id"
      pagination={false}
      scroll={{ x: 700 }}
      className="shadow-sm rounded-lg overflow-hidden border border-amber-100"
    />
  );
};
