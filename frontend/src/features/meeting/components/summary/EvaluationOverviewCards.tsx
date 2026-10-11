import React from 'react';
import { Card, Typography, Row, Col, Rate, Tag } from 'antd';
import { ReadOutlined, SmileOutlined } from '@ant-design/icons';
import type { MeetingEvaluationSummary } from '../../types/meeting.types';

const { Title, Text } = Typography;

interface Props {
  summary: MeetingEvaluationSummary;
  trainerCount: number;
  traineeCount: number;
  trainerAvgScore: number;
  traineeAvgScore: number;
}

export const EvaluationOverviewCards: React.FC<Props> = ({
  summary,
  trainerCount,
  traineeCount,
  trainerAvgScore,
  traineeAvgScore,
}) => {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      {/* 1. Tổng điểm */}
      <Col xs={24} md={8}>
        <Card style={{ height: '100%', backgroundColor: '#fafafa' }} size="small">
          <Text type="secondary" style={{ fontSize: 13 }}>
            Điểm Đánh Giá Chung
          </Text>
          <div className="flex items-baseline gap-1.5 mt-1">
            <Title level={2} style={{ margin: 0, color: '#faad14' }}>
              {summary.overall_average_score.toFixed(1)}
            </Title>
            <Text type="secondary" style={{ fontSize: 14 }}>
              / 5.0
            </Text>
          </div>
          <Rate
            allowHalf
            disabled
            value={summary.overall_average_score}
            style={{ fontSize: 15, marginTop: 4 }}
          />
          <div className="mt-2">
            <Tag color="blue" style={{ fontSize: 12 }}>
              Tổng cộng: {summary.total_evaluations} phiếu
            </Tag>
          </div>
        </Card>
      </Col>

      {/* 2. Trainer đánh giá Trainee */}
      <Col xs={24} sm={12} md={8}>
        <Card
          style={{ height: '100%', borderColor: '#ffd591', backgroundColor: '#fffbe6' }}
          size="small"
        >
          <div className="flex justify-between items-center">
            <Text strong style={{ color: '#d46b08' }}>
              <ReadOutlined style={{ marginRight: 6 }} /> Trainer đánh giá Trainee
            </Text>
            <Tag color="gold">{trainerCount} phiếu</Tag>
          </div>
          <div className="flex items-baseline gap-1.5 mt-2">
            <Title level={3} style={{ margin: 0, color: '#d46b08' }}>
              {trainerCount > 0 ? trainerAvgScore.toFixed(1) : '--'}
            </Title>
            <Text type="secondary" style={{ fontSize: 13 }}>
              / 5.0
            </Text>
          </div>
          <Rate
            allowHalf
            disabled
            value={trainerAvgScore}
            style={{ fontSize: 14, color: '#fa8c16', marginTop: 4 }}
          />
        </Card>
      </Col>

      {/* 3. Trainee đánh giá Trainer */}
      <Col xs={24} sm={12} md={8}>
        <Card
          style={{ height: '100%', borderColor: '#91d5ff', backgroundColor: '#e6f7ff' }}
          size="small"
        >
          <div className="flex justify-between items-center">
            <Text strong style={{ color: '#096dd9' }}>
              <SmileOutlined style={{ marginRight: 6 }} /> Trainee đánh giá Trainer
            </Text>
            <Tag color="blue">{traineeCount} phiếu</Tag>
          </div>
          <div className="flex items-baseline gap-1.5 mt-2">
            <Title level={3} style={{ margin: 0, color: '#096dd9' }}>
              {traineeCount > 0 ? traineeAvgScore.toFixed(1) : '--'}
            </Title>
            <Text type="secondary" style={{ fontSize: 13 }}>
              / 5.0
            </Text>
          </div>
          <Rate
            allowHalf
            disabled
            value={traineeAvgScore}
            style={{ fontSize: 14, color: '#1890ff', marginTop: 4 }}
          />
        </Card>
      </Col>
    </Row>
  );
};
