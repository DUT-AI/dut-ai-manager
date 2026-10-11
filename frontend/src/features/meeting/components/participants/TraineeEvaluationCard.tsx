import React from 'react';
import { Card, Typography, Space, Button, Tag } from 'antd';
import { HeartFilled, HeartOutlined, TrophyOutlined, StarFilled } from '@ant-design/icons';
import type { EvaluationResponse } from '../../types/meeting.types';

const { Text } = Typography;

interface Props {
  myEvalForTrainer: EvaluationResponse | null | undefined;
  onOpenMyResult: () => void;
  onOpenTraineeEval: () => void;
}

export const TraineeEvaluationCard: React.FC<Props> = ({
  myEvalForTrainer,
  onOpenMyResult,
  onOpenTraineeEval,
}) => {
  return (
    <Card
      size="small"
      className="border-indigo-100 bg-gradient-to-r from-indigo-50/70 to-blue-50/50 shadow-sm rounded-xl"
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
            {myEvalForTrainer ? (
              <HeartFilled className="text-lg text-pink-500" />
            ) : (
              <HeartOutlined className="text-lg text-indigo-500" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Text strong className="text-indigo-950 text-sm">
                Đánh giá Giảng viên (Trainer) của bạn
              </Text>
              {myEvalForTrainer ? (
                <Tag color="success" className="text-xs m-0">
                  ✓ Đã hoàn thành {myEvalForTrainer.is_anonymous ? '(Ẩn danh)' : ''} (⭐{' '}
                  {myEvalForTrainer.average_score.toFixed(1)}/5)
                </Tag>
              ) : (
                <Tag color="warning" className="text-xs m-0">
                  Chưa đánh giá
                </Tag>
              )}
            </div>
            <Text type="secondary" className="text-xs text-indigo-700 block mt-0.5">
              {myEvalForTrainer
                ? `Bạn đã gửi đánh giá ${
                    myEvalForTrainer.is_anonymous ? 'ẩn danh ' : ''
                  }cho Trainer. Bạn có thể mở khóa xem bảng điểm rèn luyện cá nhân!`
                : 'Hãy gửi đánh giá & nhận xét cho Trainer để mở khóa xem điểm rèn luyện cá nhân của bạn.'}
            </Text>
          </div>
        </div>
        <Space wrap className="shrink-0">
          <Button
            icon={<TrophyOutlined className="text-yellow-600" />}
            onClick={onOpenMyResult}
            className="bg-white border-indigo-200 text-indigo-800 hover:!border-indigo-400"
            size="small"
          >
            Xem Điểm của tôi
          </Button>
          <Button
            type="primary"
            icon={<StarFilled />}
            onClick={onOpenTraineeEval}
            className={
              myEvalForTrainer
                ? 'bg-indigo-600 hover:!bg-indigo-500'
                : 'bg-amber-600 hover:!bg-amber-500'
            }
            size="small"
          >
            {myEvalForTrainer ? 'Sửa đánh giá Trainer' : 'Đánh giá Trainer ngay'}
          </Button>
        </Space>
      </div>
    </Card>
  );
};
