import React from 'react';
import { Card, Avatar, Typography, Row, Col, Rate } from 'antd';
import { ReadOutlined } from '@ant-design/icons';
import type { MeetingOverallEvaluationResponse } from '../../types/meeting.types';
import { CRITERIA_LABEL_MAP } from './evaluationConstants';

const { Title, Text, Paragraph } = Typography;

interface Props {
  overallEvaluation: MeetingOverallEvaluationResponse;
}

export const MeetingOverallEvaluationCard: React.FC<Props> = ({ overallEvaluation }) => {
  return (
    <Card
      style={{
        marginBottom: 16,
        background: 'linear-gradient(135deg, #fff7e6 0%, #ffffff 100%)',
        borderColor: '#ffd591',
        borderRadius: 8,
      }}
      size="small"
    >
      <div className="flex justify-between items-center flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Avatar
            icon={<ReadOutlined />}
            src={overallEvaluation.trainer?.avatar_url}
            style={{ backgroundColor: '#fa8c16' }}
          />
          <div>
            <Text strong style={{ fontSize: 14, color: '#d46b08' }}>
              Đánh Giá Tổng Thể Buổi Học từ Trainer ({overallEvaluation.trainer?.name || 'Trainer'})
            </Text>
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
              Quan hệ 1 - 1 (Đánh giá chung cho cả buổi học)
            </div>
          </div>
        </div>
        <div className="flex items-baseline gap-1.5">
          <Title level={3} style={{ margin: 0, color: '#fa8c16' }}>
            {overallEvaluation.average_score.toFixed(1)}
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            / 5.0
          </Text>
          <Rate
            allowHalf
            disabled
            value={overallEvaluation.average_score}
            style={{ fontSize: 14, color: '#fa8c16', marginLeft: 6 }}
          />
        </div>
      </div>

      {/* Chi tiết 4 tiêu chí của meeting */}
      <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
        {overallEvaluation.scores.map((s) => (
          <Col xs={24} sm={12} md={6} key={s.criteria_code}>
            <div
              style={{
                background: '#fff',
                padding: '8px 12px',
                borderRadius: 6,
                border: '1px solid #ffe7ba',
              }}
            >
              <Text strong style={{ fontSize: 12, display: 'block', color: '#595959' }}>
                {s.criteria_name || CRITERIA_LABEL_MAP[s.criteria_code] || s.criteria_code}
              </Text>
              <div className="flex justify-between items-center mt-1">
                <Rate disabled value={s.score} style={{ fontSize: 12, color: '#fa8c16' }} />
                <Text strong style={{ color: '#d46b08', fontSize: 13 }}>
                  {s.score}.0
                </Text>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      {overallEvaluation.general_feedback && (
        <div
          style={{
            marginTop: 12,
            padding: '8px 12px',
            background: '#fff',
            borderRadius: 6,
            border: '1px solid #ffe7ba',
          }}
        >
          <Text strong style={{ fontSize: 12, color: '#8c8c8c' }}>
            Nhận xét chung của Trainer:
          </Text>
          <Paragraph
            style={{
              margin: '4px 0 0 0',
              color: '#262626',
              fontSize: 13,
              whiteSpace: 'pre-wrap',
            }}
          >
            {overallEvaluation.general_feedback}
          </Paragraph>
        </div>
      )}
    </Card>
  );
};
