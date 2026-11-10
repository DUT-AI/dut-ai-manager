import React from 'react';
import { Modal, Avatar, Typography, Tag, Rate, Card, Divider } from 'antd';
import { UserOutlined, CalendarOutlined, StarFilled } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { EvaluationResponse } from '../types/meeting.types';

const { Text, Title, Paragraph } = Typography;

interface Props {
  open: boolean;
  evaluation?: EvaluationResponse | null;
  onClose: () => void;
}

export const EvaluationDetailModal: React.FC<Props> = ({
  open,
  evaluation,
  onClose,
}) => {
  if (!evaluation) return null;

  const isAnonymous = evaluation.is_anonymous;
  const isTrainerEval = evaluation.evaluation_type === 'TRAINER_TO_TRAINEE';
  const reviewerName = isAnonymous
    ? 'Học viên ẩn danh'
    : evaluation.reviewer?.name || (isTrainerEval ? 'Giảng viên / Trainer' : 'Học viên');
  const targetName = evaluation.target_user?.name || (isTrainerEval ? 'Học viên' : 'Giảng viên');

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <StarFilled style={{ color: '#faad14' }} />
          <span>Chi tiết đánh giá buổi học</span>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      destroyOnClose
      width={600}
      className="evaluation-detail-modal"
    >
      <div className="py-2 space-y-4">
        {/* Reviewer & Target Card */}
        <div className="p-4 bg-gray-50/80 rounded-xl border border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Avatar
              size={48}
              icon={<UserOutlined />}
              src={isAnonymous ? null : evaluation.reviewer?.avatar_url}
              style={{
                backgroundColor: isAnonymous ? '#8c8c8c' : isTrainerEval ? '#fa8c16' : '#1890ff',
              }}
            />
            <div>
              <div className="flex items-center gap-2">
                <Text strong className="text-base text-gray-800">
                  {reviewerName}
                </Text>
                {isAnonymous && <Tag color="purple">Ẩn danh</Tag>}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                Đánh giá cho:{' '}
                <Text strong className="text-gray-700">
                  {targetName}
                </Text>
              </div>
            </div>
          </div>

          <div className="text-left sm:text-right border-t sm:border-t-0 pt-2 sm:pt-0 border-gray-200">
            <div className="flex items-center sm:justify-end gap-1.5">
              <Rate disabled allowHalf value={evaluation.average_score} style={{ fontSize: 14 }} />
              <span className="text-base font-bold text-amber-500">
                {evaluation.average_score.toFixed(1)}
              </span>
            </div>
            <div className="text-xs text-gray-400 flex items-center sm:justify-end gap-1 mt-1">
              <CalendarOutlined />
              <span>{dayjs(evaluation.created_at).format('DD/MM/YYYY HH:mm')}</span>
            </div>
          </div>
        </div>

        {/* Detailed Criteria Scores */}
        <div>
          <Title level={5} className="!mb-3 text-sm font-semibold text-gray-700">
            Chi tiết điểm theo tiêu chí
          </Title>
          <div className="space-y-2.5">
            {evaluation.scores && evaluation.scores.length > 0 ? (
              evaluation.scores.map((scoreItem) => (
                <div
                  key={scoreItem.criteria_code}
                  className="p-3 bg-white border border-gray-100 rounded-lg shadow-2xs flex items-center justify-between gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <Text strong className="text-sm block text-gray-800 truncate">
                      {scoreItem.criteria_name || scoreItem.criteria_code}
                    </Text>
                    {scoreItem.criteria_description && (
                      <Text type="secondary" className="text-xs line-clamp-1">
                        {scoreItem.criteria_description}
                      </Text>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Rate disabled value={scoreItem.score} count={5} style={{ fontSize: 13 }} />
                    <Tag color="gold" className="font-semibold text-xs py-0.5 px-1.5 m-0">
                      {scoreItem.score} sao
                    </Tag>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-gray-400 text-xs italic bg-gray-50 rounded-lg">
                Không có tiêu chí chi tiết
              </div>
            )}
          </div>
        </div>

        {/* Feedback / Comments */}
        {evaluation.feedback_text && (
          <div>
            <Title level={5} className="!mb-2 text-sm font-semibold text-gray-700">
              Nhận xét & Góp ý
            </Title>
            <Card size="small" className="bg-blue-50/30 border-blue-100 rounded-lg">
              <Paragraph className="!mb-0 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                {evaluation.feedback_text}
              </Paragraph>
            </Card>
          </div>
        )}
      </div>
    </Modal>
  );
};
