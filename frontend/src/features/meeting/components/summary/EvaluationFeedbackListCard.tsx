import React, { useState } from 'react';
import { Card, Typography, Segmented, Empty, List, Avatar, Tag, Rate } from 'antd';
import { MessageOutlined, UserOutlined } from '@ant-design/icons';
import type { EvaluationResponse } from '../../types/meeting.types';

const { Text, Paragraph } = Typography;

interface Props {
  evaluations: EvaluationResponse[];
}

export const EvaluationFeedbackListCard: React.FC<Props> = ({ evaluations }) => {
  const [feedbackFilter, setFeedbackFilter] = useState<'ALL' | 'TRAINER_TO_TRAINEE' | 'TRAINEE_TO_TRAINER'>('ALL');

  const feedbackList = evaluations.filter((e) => Boolean(e.feedback_text));
  const filteredFeedback = feedbackList.filter((e) => {
    if (feedbackFilter === 'ALL') return true;
    return e.evaluation_type === feedbackFilter;
  });

  return (
    <Card
      title={
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span>
            <MessageOutlined style={{ marginRight: 8, color: '#722ed1' }} />
            Ý kiến đóng góp & Nhận xét
          </span>
          <Segmented
            size="small"
            value={feedbackFilter}
            onChange={(val) => setFeedbackFilter(val as any)}
            options={[
              { label: 'Tất cả', value: 'ALL' },
              { label: 'Trainer ➜ Trainee', value: 'TRAINER_TO_TRAINEE' },
              { label: 'Trainee ➜ Trainer', value: 'TRAINEE_TO_TRAINER' },
            ]}
          />
        </div>
      }
      size="small"
    >
      {filteredFeedback.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Chưa có ý kiến nhận xét nào"
          style={{ margin: '16px 0' }}
        />
      ) : (
        <List
          itemLayout="horizontal"
          dataSource={filteredFeedback}
          renderItem={(item) => {
            const isTrainerEval = item.evaluation_type === 'TRAINER_TO_TRAINEE';
            const reviewerName = item.is_anonymous
              ? 'Học viên ẩn danh'
              : item.reviewer?.name || (isTrainerEval ? 'Trainer' : 'Trainee');

            return (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <Avatar
                      icon={<UserOutlined />}
                      src={item.is_anonymous ? null : item.reviewer?.avatar_url}
                      style={{
                        backgroundColor: item.is_anonymous
                          ? '#8c8c8c'
                          : isTrainerEval
                          ? '#fa8c16'
                          : '#1890ff',
                      }}
                    />
                  }
                  title={
                    <div className="flex items-center gap-2 flex-wrap">
                      <Text strong>{reviewerName}</Text>
                      {item.is_anonymous && <Tag color="default">Ẩn danh</Tag>}
                      <Tag color={isTrainerEval ? 'gold' : 'cyan'}>
                        {isTrainerEval ? 'Trainer ➜ Trainee' : 'Trainee ➜ Trainer'}
                      </Tag>
                      {item.target_user?.name && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          đánh giá cho: <Text strong>{item.target_user.name}</Text>
                        </Text>
                      )}
                      <Rate disabled value={item.average_score} style={{ fontSize: 12, marginLeft: 'auto' }} />
                    </div>
                  }
                  description={
                    <Paragraph style={{ margin: '6px 0 0 0', color: '#595959', whiteSpace: 'pre-wrap' }}>
                      {item.feedback_text}
                    </Paragraph>
                  }
                />
              </List.Item>
            );
          }}
        />
      )}
    </Card>
  );
};
