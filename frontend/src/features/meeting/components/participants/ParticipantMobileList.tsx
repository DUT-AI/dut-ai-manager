import React from 'react';
import { Card, Avatar, Tag, Typography, Image, List, Empty, Button } from 'antd';
import {
  UserOutlined,
  CrownOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  StarFilled,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type {
  ParticipantResponse,
  EvaluationResponse,
  MeetingResponse,
  MeetingDetailResponse,
  MeetingOverallEvaluationResponse,
} from '../../types/meeting.types';
import { ParticipantRole } from '../../types/meeting.types';
import { ParticipantStatusTag } from '../ParticipantStatusTag';
import { ParticipantActionButtons } from '../ParticipantActionButtons';

const { Text } = Typography;

interface Props {
  meeting: MeetingResponse | MeetingDetailResponse;
  trainers?: ParticipantResponse[];
  trainees?: ParticipantResponse[];
  participants?: ParticipantResponse[];
  currentUserId?: number;
  isTrainer: boolean;
  isEnded: boolean;
  traineeEvalsByReviewerId: Map<number, EvaluationResponse>;
  onEditStatus: (participant: ParticipantResponse) => void;
  onOpenOverallEvaluation?: () => void;
  overallEval?: MeetingOverallEvaluationResponse | null;
}

export const ParticipantMobileList: React.FC<Props> = ({
  meeting,
  trainers,
  trainees,
  participants,
  isTrainer,
  isEnded,
  traineeEvalsByReviewerId,
  onEditStatus,
  onOpenOverallEvaluation,
  overallEval,
}) => {
  // Chuẩn hóa danh sách trainers và trainees
  const actualTrainers =
    trainers ??
    (participants || []).filter((p) => p.role === ParticipantRole.TRAINER);
  const actualTrainees =
    trainees ??
    (participants || []).filter((p) => p.role !== ParticipantRole.TRAINER);

  const renderParticipantCard = (record: ParticipantResponse, isTrainerItem: boolean) => {
    const traineeEval = traineeEvalsByReviewerId.get(record.user_id);

    return (
      <Card
        size="small"
        className={`w-full shadow-xs rounded-xl transition-colors mb-3 ${
          isTrainerItem ? 'border-amber-200/80 bg-amber-50/20' : 'border-gray-100 bg-white'
        }`}
        styles={{ body: { padding: '12px' } }}
      >
        {/* Header: User Info & Status */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <Avatar
              src={record.user_avatar_url}
              icon={<UserOutlined />}
              size={38}
              className={`shrink-0 border ${
                isTrainerItem ? 'border-amber-300' : 'border-gray-100'
              }`}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <Text strong className="text-sm truncate block max-w-[170px]">
                  {record.user_name || `User #${record.user_id}`}
                </Text>
                {isTrainerItem && (
                  <Tag color="gold" className="text-[10px] m-0 px-1.5 leading-4">
                    <CrownOutlined className="mr-0.5" /> Trainer
                  </Tag>
                )}
              </div>
              {record.check_in_at ? (
                <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-0.5">
                  <ClockCircleOutlined className="text-emerald-500" />
                  <span>Check-in: {dayjs(record.check_in_at).format('HH:mm')}</span>
                </div>
              ) : (
                <span className="text-[11px] text-gray-400 block mt-0.5">Chưa điểm danh</span>
              )}
            </div>
          </div>

          <div className="shrink-0 text-right">
            <ParticipantStatusTag status={record.status} />
          </div>
        </div>

        {/* Middle Section: Evaluation Scores & Card Image */}
        <div className="mt-2.5 pt-2 border-t border-gray-100 flex items-center justify-between text-xs gap-2">
          {meeting.enable_evaluation ? (
            <div className="flex items-center gap-2 flex-wrap">
              {!isTrainerItem && (
                traineeEval ? (
                  <Tag color="cyan" className="m-0 text-[11px] py-0 px-1.5 rounded flex items-center gap-1">
                    <CheckCircleOutlined /> Đã đánh giá Trainer
                  </Tag>
                ) : (
                  <Tag color="default" className="m-0 text-[11px] py-0 px-1.5 rounded text-gray-400">
                    Chưa đánh giá Trainer
                  </Tag>
                )
              )}
            </div>
          ) : (
            <div />
          )}

          {record.link_image && (
            <div className="shrink-0 flex items-center gap-1">
              <Image
                src={record.link_image}
                alt="Checkin"
                width={28}
                height={28}
                className="rounded-md object-cover border border-gray-100"
                preview={{ mask: <span className="text-[9px]">Xem</span> }}
              />
            </div>
          )}
        </div>

        {/* Footer: Actions */}
        <div className="mt-2.5 pt-2 border-t border-gray-100 flex justify-end">
          <ParticipantActionButtons
            meetingId={meeting.id}
            record={record}
            isTrainer={isTrainer}
            onEditStatus={onEditStatus}
          />
        </div>
      </Card>
    );
  };

  return (
    <div className="space-y-5">
      {/* 1. Nhóm Giảng viên */}
      <div>
        <div className="flex items-center gap-1.5 mb-2 px-1">
          <CrownOutlined className="text-amber-500" />
          <span className="font-semibold text-xs text-gray-700 uppercase tracking-wider">
            Giảng viên ({actualTrainers.length})
          </span>
        </div>
        {actualTrainers.length === 0 ? (
          <div className="p-3 bg-gray-50 border border-gray-100 rounded-xl text-center text-xs text-gray-400">
            Buổi tự học nhóm (không có Trainer)
          </div>
        ) : (
          actualTrainers.map((t) => renderParticipantCard(t, true))
        )}
      </div>

      {/* 2. Nhóm Học viên */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2 px-1">
          <div className="flex items-center gap-1.5">
            <UserOutlined className="text-blue-500" />
            <span className="font-semibold text-xs text-gray-700 uppercase tracking-wider">
              Học viên ({actualTrainees.length})
            </span>
          </div>
          {meeting.enable_evaluation && isTrainer && onOpenOverallEvaluation && (
            <Button
              type="primary"
              size="small"
              icon={<StarFilled />}
              onClick={onOpenOverallEvaluation}
              className={
                overallEval
                  ? "!bg-emerald-600 hover:!bg-emerald-500 !text-white border-none text-xs rounded-full"
                  : "!bg-amber-500 hover:!bg-amber-400 !text-white border-none text-xs rounded-full"
              }
            >
              {overallEval ? '✓ Đã đánh giá' : 'Đánh giá buổi học'}
            </Button>
          )}
        </div>
        {actualTrainees.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Chưa có học viên nào"
            className="my-4"
          />
        ) : (
          <List
            dataSource={actualTrainees}
            pagination={
              actualTrainees.length > 10
                ? { pageSize: 10, size: 'small', align: 'center' }
                : false
            }
            split={false}
            renderItem={(trainee) => (
              <List.Item className="!p-0 !mb-0">
                {renderParticipantCard(trainee, false)}
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
};

export default ParticipantMobileList;
