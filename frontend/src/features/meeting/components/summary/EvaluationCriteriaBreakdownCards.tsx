import React from 'react';
import { Card, Typography, Row, Col, Progress, Empty, Tag } from 'antd';
import { ReadOutlined, SmileOutlined } from '@ant-design/icons';
import type { CriteriaBreakdown } from '../../types/meeting.types';
import { CRITERIA_LABEL_MAP } from './evaluationConstants';

const { Text } = Typography;

interface Props {
  trainerCriteria: CriteriaBreakdown[];
  traineeCriteria: CriteriaBreakdown[];
}

const renderCriteriaList = (
  items: CriteriaBreakdown[],
  themeColor: string,
  emptyText: string
) => {
  if (items.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={emptyText}
        style={{ margin: '16px 0' }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3.5">
      {items.map((item) => {
        const label =
          item.criteria_name || CRITERIA_LABEL_MAP[item.criteria_code] || item.criteria_code;
        const percent = Math.round((item.average_score / 5) * 100);

        return (
          <div key={item.criteria_code}>
            <div className="flex justify-between items-baseline mb-1">
              <div className="pr-2">
                <Text strong style={{ fontSize: 13 }}>
                  {label}
                </Text>
                {item.criteria_description && (
                  <Text
                    type="secondary"
                    style={{ display: 'block', fontSize: 12, color: '#8c8c8c' }}
                  >
                    {item.criteria_description}
                  </Text>
                )}
              </div>
              <div className="text-right shrink-0">
                <Text strong style={{ fontSize: 14, color: themeColor }}>
                  {item.average_score.toFixed(1)}
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {' '}/ 5 ({item.count} lượt)
                </Text>
              </div>
            </div>
            <Progress
              percent={percent}
              strokeColor={themeColor}
              showInfo={false}
              size="small"
            />
          </div>
        );
      })}
    </div>
  );
};

export const EvaluationCriteriaBreakdownCards: React.FC<Props> = ({
  trainerCriteria,
  traineeCriteria,
}) => {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      {/* 1. Trainer đánh giá Trainee */}
      <Col xs={24} lg={12}>
        <Card
          title={
            <div className="flex items-center justify-between">
              <span>
                <ReadOutlined style={{ color: '#fa8c16', marginRight: 8 }} />
                Tiêu chí Trainer đánh giá Trainee
              </span>
              <Tag color="gold">Trainer ➜ Trainee</Tag>
            </div>
          }
          size="small"
          style={{ height: '100%' }}
        >
          {renderCriteriaList(
            trainerCriteria,
            '#fa8c16',
            'Chưa có dữ liệu đánh giá từ Trainer'
          )}
        </Card>
      </Col>

      {/* 2. Trainee đánh giá Trainer */}
      <Col xs={24} lg={12}>
        <Card
          title={
            <div className="flex items-center justify-between">
              <span>
                <SmileOutlined style={{ color: '#1890ff', marginRight: 8 }} />
                Tiêu chí Trainee đánh giá Trainer
              </span>
              <Tag color="blue">Trainee ➜ Trainer</Tag>
            </div>
          }
          size="small"
          style={{ height: '100%' }}
        >
          {renderCriteriaList(
            traineeCriteria,
            '#1890ff',
            'Chưa có dữ liệu đánh giá từ Học viên'
          )}
        </Card>
      </Col>
    </Row>
  );
};
