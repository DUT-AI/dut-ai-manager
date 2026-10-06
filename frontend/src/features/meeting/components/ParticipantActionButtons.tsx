import React, { useState } from 'react';
import { Space, Button, Popconfirm, Tooltip, message } from 'antd';
import {
  CheckOutlined,
  EditOutlined,
  StarOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ParticipantResponse } from '../types/meeting.types';
import { ParticipantStatus } from '../types/meeting.types';
import { useUpdateParticipantStatus, useMeetingDetail } from '../hooks/useMeetings';

interface Props {
  meetingId: number;
  record: ParticipantResponse;
  isTrainer: boolean;
  isEnded: boolean;
  enableEvaluation?: boolean;
  onEditStatus: (participant: ParticipantResponse) => void;
  onEvaluate: (participant: ParticipantResponse) => void;
}

export const ParticipantActionButtons: React.FC<Props> = ({
  meetingId,
  record,
  isTrainer,
  isEnded,
  enableEvaluation,
  onEditStatus,
  onEvaluate,
}) => {
  const [loading, setLoading] = useState(false);
  const updateParticipantStatusMutation = useUpdateParticipantStatus();
  const { refetch } = useMeetingDetail(meetingId);

  const isJoined =
    record.status === ParticipantStatus.JOINED ||
    record.status === ParticipantStatus.LATE_EXCUSED ||
    record.status === ParticipantStatus.LATE_UNEXCUSED ||
    record.status === ParticipantStatus.COMPLETED;

  const handleQuickCheckIn = async (isCheckIn: boolean) => {
    try {
      setLoading(true);
      if (isCheckIn) {
        await updateParticipantStatusMutation.mutateAsync({
          meetingId,
          userId: record.user_id,
          payload: {
            status: ParticipantStatus.JOINED,
            check_in_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
          },
        });
        message.success(`Đã điểm danh cho ${record.user_name || 'học viên'}`);
      } else {
        await updateParticipantStatusMutation.mutateAsync({
          meetingId,
          userId: record.user_id,
          payload: {
            status: ParticipantStatus.NOT_JOINED,
            check_in_at: null,
            check_out_at: null,
          },
        });
        message.success(`Đã hủy điểm danh cho ${record.user_name || 'học viên'}`);
      }
      refetch();
    } catch {
      message.error(isCheckIn ? 'Điểm danh thất bại' : 'Hủy điểm danh thất bại');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space size="small">
      {isTrainer && (
        <>
          {!isJoined ? (
            <Button
              type="primary"
              size="small"
              icon={<ThunderboltOutlined />}
              className="bg-emerald-600 hover:!bg-emerald-500 text-white font-medium"
              loading={loading}
              onClick={() => handleQuickCheckIn(true)}
            >
              Check-in
            </Button>
          ) : (
            <Popconfirm
              title="Hủy điểm danh?"
              description={`Bạn có chắc muốn hủy điểm danh của ${record.user_name || 'học viên này'}?`}
              onConfirm={() => handleQuickCheckIn(false)}
              okText="Hủy điểm danh"
              cancelText="Đóng"
            >
              <Button
                size="small"
                icon={<CheckOutlined />}
                className="text-emerald-700 bg-emerald-50 border-emerald-300 hover:!bg-emerald-100 font-medium"
                loading={loading}
              >
                Đã Check-in
              </Button>
            </Popconfirm>
          )}
        </>
      )}

      {isTrainer && (
        enableEvaluation ? (
          <Tooltip
            title={
              record.status === ParticipantStatus.ABSENT_EXCUSED ||
              record.status === ParticipantStatus.ABSENT_UNEXCUSED
                ? 'Học viên vắng mặt không thể đánh giá'
                : 'Chấm điểm đánh giá học viên này'
            }
          >
            <Button
              icon={<StarOutlined className="text-amber-500" />}
              size="small"
              type="dashed"
              disabled={
                record.status === ParticipantStatus.ABSENT_EXCUSED ||
                record.status === ParticipantStatus.ABSENT_UNEXCUSED
              }
              className="hover:!border-amber-400 text-amber-700 bg-amber-50/50"
              onClick={() => onEvaluate(record)}
            >
              Đánh giá
            </Button>
          </Tooltip>
        ) : (
          <Tooltip title="Bật 'Đánh giá 2 chiều' để chấm điểm học viên">
            <Button
              icon={<StarOutlined className="text-gray-300" />}
              size="small"
              type="dashed"
              disabled
              className="opacity-60"
            >
              Đánh giá
            </Button>
          </Tooltip>
        )
      )}

      {isTrainer && (
        <Tooltip title="Chỉnh sửa chi tiết trạng thái">
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => onEditStatus(record)}
          />
        </Tooltip>
      )}
    </Space>
  );
};
