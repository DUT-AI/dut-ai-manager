import React from 'react';
import { Card, Avatar, Tag, Typography, Image, List, Empty } from 'antd';
import { UserOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
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

export const ParticipantMobileList: React.FC<Props> = ({
  meeting,
  participants,
  isTrainer,
  isEnded,
  trainerEvalsByTraineeId,
  traineeEvalsByReviewerId,
  onEditStatus,
  onEvaluate,
}) => {
  if (participants.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="Chưa có thành viên nào"
        className="my-6"
      />
    );
  }

  return (
    <List
      dataSource={participants}
      pagination={participants.length > 10 ? { pageSize: 10, size: 'small', align: 'center' } : false}
      split={false}
      renderItem={(record) => {
        const trainerEval = trainerEvalsByTraineeId.get(record.user_id);
        const traineeEval = traineeEvalsByReviewerId.get(record.user_id);

        return (
          <List.Item className="!p-0 !mb-3">
            <Card
              size="small"
              className="w-full shadow-xs border-gray-100 rounded-xl hover:border-indigo-100 transition-colors"
              styles={{ body: { padding: '12px' } }}
            >
              {/* Header: User Info & Status */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  <Avatar
                    src={record.user_avatar_url}
                    icon={<UserOutlined />}
                    size={38}
                    className="shrink-0 border border-gray-100"
                  />
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Text strong className="text-sm truncate block max-w-[170px]">
                        {record.user_name || `User #${record.user_id}`}
                      </Text>
                      {record.user_id === meeting.created_by && (
                        <Tag color="gold" className="text-[10px] m-0 px-1.5 leading-4">
                          Trainer
                        </Tag>
                      )}
                    </div>
                    {record.check_in_time ? (
                      <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-0.5">
                        <ClockCircleOutlined className="text-emerald-500" />
                        <span>Check-in: {dayjs(record.check_in_time).format('HH:mm')}</span>
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
              <div className="mt-2.5 pt-2 border-t border-gray-50 flex items-center justify-between text-xs gap-2">
                {meeting.enable_evaluation ? (
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Trainer chấm Trainee */}
                    {trainerEval ? (
                      <Tag color="purple" className="m-0 text-[11px] py-0 px-1.5 rounded">
                        Trainer: ★ {trainerEval.average_score.toFixed(1)}
                      </Tag>
                    ) : (
                      <Tag color="default" className="m-0 text-[11px] py-0 px-1.5 rounded text-gray-400">
                        Chưa chấm
                      </Tag>
                    )}

                    {/* Trainee chấm Trainer */}
                    {traineeEval ? (
                      <Tag color="cyan" className="m-0 text-[11px] py-0 px-1.5 rounded flex items-center gap-1">
                        <CheckCircleOutlined /> Đã đánh giá
                      </Tag>
                    ) : null}
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
              <div className="mt-2.5 pt-2 border-t border-gray-50 flex justify-end">
                <ParticipantActionButtons
                  meetingId={meeting.id}
                  record={record}
                  isTrainer={isTrainer}
                  isEnded={isEnded}
                  enableEvaluation={meeting.enable_evaluation}
                  existingEvaluation={trainerEval}
                  onEditStatus={onEditStatus}
                  onEvaluate={onEvaluate}
                />
              </div>
            </Card>
          </List.Item>
        );
      }}
    />
  );
};

export default ParticipantMobileList;
