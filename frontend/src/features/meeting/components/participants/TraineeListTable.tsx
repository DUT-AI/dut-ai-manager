import React from 'react';
import { Table, Avatar, Typography, Image, Tag, Empty, Button, Tooltip } from 'antd';
import { UserOutlined, CheckCircleOutlined, StarFilled, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import type {
  ParticipantResponse,
  EvaluationResponse,
  MeetingResponse,
  MeetingDetailResponse,
  MeetingOverallEvaluationResponse,
} from '../../types/meeting.types';
import { ParticipantStatusTag } from '../ParticipantStatusTag';
import { ParticipantActionButtons } from '../ParticipantActionButtons';

const { Text } = Typography;

interface Props {
  meeting: MeetingResponse | MeetingDetailResponse;
  trainees: ParticipantResponse[];
  currentUserId?: number;
  isTrainer: boolean;
  isEnded: boolean;
  traineeEvalsByReviewerId: Map<number, EvaluationResponse>;
  onEditStatus: (participant: ParticipantResponse) => void;
  onOpenOverallEvaluation?: () => void;
  overallEval?: MeetingOverallEvaluationResponse | null;
  onViewEvaluation?: (evaluation: EvaluationResponse) => void;
}

export const TraineeListTable: React.FC<Props> = ({
  meeting,
  trainees,
  currentUserId,
  isTrainer,
  isEnded,
  traineeEvalsByReviewerId,
  onEditStatus,
  onOpenOverallEvaluation,
  overallEval,
  onViewEvaluation,
}) => {
  const columns: ColumnsType<ParticipantResponse> = [
    {
      title: 'Học viên / Người tham gia',
      key: 'user',
      render: (_: unknown, record: ParticipantResponse) => (
        <div className="flex items-center gap-3">
          <Avatar
            src={record.user_avatar_url}
            icon={<UserOutlined />}
            size="default"
            className="border border-blue-200"
          />
          <div>
            <Text strong className="block text-sm text-gray-800">
              {record.user_name || `User #${record.user_id}`}
            </Text>
            <span className="text-[11px] text-gray-400">
              ID: #{record.user_id}
            </span>
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
        const aTime =
          a.check_out_at || (isEnded && a.check_in_at ? meeting.end_time : null);
        const bTime =
          b.check_out_at || (isEnded && b.check_in_at ? meeting.end_time : null);
        if (!aTime) return 1;
        if (!bTime) return -1;
        return dayjs(aTime).unix() - dayjs(bTime).unix();
      },
    },
    ...(meeting.enable_evaluation
      ? [
        {
          title: 'Đánh giá Giảng viên',
          key: 'trainee_eval',
          render: (_: unknown, record: ParticipantResponse) => {
            const existing = traineeEvalsByReviewerId.get(record.user_id);
            if (existing) {
              const isAnonymous = existing.is_anonymous;
              return (
                <div className="flex items-center gap-1.5">
                  <Tag
                    color={isAnonymous ? 'purple' : 'blue'}
                    icon={<CheckCircleOutlined />}
                    className={`text-xs py-0.5 px-2 m-0 ${
                      onViewEvaluation ? 'cursor-pointer hover:opacity-85' : ''
                    }`}
                    onClick={() => onViewEvaluation && onViewEvaluation(existing)}
                  >
                    {isAnonymous ? 'Đã gửi (Ẩn danh)' : 'Đã gửi'}
                    {record.user_id === currentUserId || isTrainer
                      ? ` (⭐ ${existing.average_score.toFixed(1)})`
                      : ''}
                  </Tag>
                  {onViewEvaluation && (
                    <Tooltip title="Xem chi tiết đánh giá">
                      <Button
                        type="text"
                        size="small"
                        icon={<EyeOutlined />}
                        className="text-gray-400 hover:text-blue-600 h-6 w-6 p-0"
                        onClick={() => onViewEvaluation(existing)}
                      />
                    </Tooltip>
                  )}
                </div>
              );
            }
            return (
              <Tag color="default" className="text-xs py-0.5 px-2 m-0">
                Chưa gửi
              </Tag>
            );
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
          onEditStatus={onEditStatus}
        />
      ),
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mt-3">
      <div className="p-3.5 sm:p-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2 bg-blue-50/40">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          <h4 className="m-0 text-sm font-semibold text-gray-800">
            Danh sách Học viên ({trainees.length})
          </h4>
        </div>

        {meeting.enable_evaluation && isTrainer && onOpenOverallEvaluation && (
          <Button
            type="primary"
            icon={<StarFilled />}
            onClick={onOpenOverallEvaluation}
            size="middle"
            className={
              overallEval
                ? "!bg-emerald-600 hover:!bg-emerald-500 !text-white border-none font-medium shadow-sm rounded-full"
                : "!bg-amber-500 hover:!bg-amber-400 !text-white border-none font-medium shadow-sm rounded-full"
            }
          >
            {overallEval ? '✓ Đã đánh giá buổi học' : 'Trainer đánh giá buổi học'}
          </Button>
        )}
      </div>
      <Table
        columns={columns}
        dataSource={trainees}
        rowKey="user_id"
        pagination={false}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="Chưa có học viên nào trong buổi học"
            />
          ),
        }}
      />
    </div>
  );
};
