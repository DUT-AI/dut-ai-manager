import React, { useEffect, useState } from 'react';
import { Card, Progress, Rate, Typography, Spin, Empty, Tag, Divider, List, Avatar } from 'antd';
import { StarFilled, UserOutlined } from '@ant-design/icons';
import { meetingService } from '../services/meeting.service';
import type { MeetingEvaluationSummary } from '../types/meeting.types';

const { Title, Text, Paragraph } = Typography;

interface Props {
  meetingId: number;
}

const CRITERIA_LABEL_MAP: Record<string, string> = {
  ATTENDANCE_CONDUCT: 'Chuyên cần & Tác phong',
  INTERACTION_CONTRIBUTION: 'Mức độ Tương tác & Đóng góp',
  ABSORPTION_COMPREHENSION: 'Mức độ Tiếp thu & Hiểu bài',
  PRE_CLASS_PREPARATION: 'Mức độ Chuẩn bị bài',
  CONTENT_QUALITY: 'Chất lượng Nội dung',
  TEACHING_METHOD: 'Phương pháp Giảng dạy',
  CLASS_ATMOSPHERE: 'Không khí Lớp học',
  PRACTICAL_VALUE: 'Giá trị Thực tế',
};

export const MeetingEvaluationSummaryView: React.FC<Props> = ({ meetingId }) => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<MeetingEvaluationSummary | null>(null);

  useEffect(() => {
    fetchSummary();
  }, [meetingId]);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await meetingService.getMeetingEvaluationSummary(meetingId);
      if (res.is_success && res.data) {
        setSummary(res.data);
      }
    } catch (err) {
      console.error('Failed to load evaluation summary', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin tip="Đang tải báo cáo đánh giá..." />
      </div>
    );
  }

  if (!summary || summary.total_evaluations === 0) {
    return (
      <Empty
        description="Chưa có đánh giá nào cho buổi học này"
        style={{ padding: '24px 0' }}
      />
    );
  }

  return (
    <div>
      {/* Overview Card */}
      <Card style={{ marginBottom: 16, backgroundColor: '#fafafa' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <Text type="secondary">Điểm Đánh Giá Trung Bình</Text>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 4 }}>
              <Title level={2} style={{ margin: 0, color: '#faad14' }}>
                {summary.overall_average_score.toFixed(1)}
              </Title>
              <Text type="secondary" style={{ fontSize: 16 }}>/ 5.0</Text>
            </div>
            <Rate allowHalf disabled value={summary.overall_average_score} style={{ fontSize: 18 }} />
          </div>

          <div style={{ textAlign: 'right' }}>
            <Tag color="blue" style={{ fontSize: 14, padding: '4px 10px' }}>
              Tổng cộng: {summary.total_evaluations} phiếu đánh giá
            </Tag>
          </div>
        </div>
      </Card>

      {/* Criteria Breakdown */}
      <Card title="Phân tích chi tiết theo Tiêu chí" size="small" style={{ marginBottom: 16 }}>
        {summary.criteria_breakdown.map((item) => {
          const label = item.criteria_name || CRITERIA_LABEL_MAP[item.criteria_code] || item.criteria_code;
          const percent = Math.round((item.average_score / 5) * 100);
          return (
            <div key={item.criteria_code} style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}>
                <div>
                  <Text strong style={{ fontSize: 13 }}>{label}</Text>
                  {item.criteria_description && (
                    <Text type="secondary" style={{ display: 'block', fontSize: 11, color: '#8c8c8c' }}>
                      {item.criteria_description}
                    </Text>
                  )}
                </div>
                <Text type="secondary" style={{ fontSize: 12, flexShrink: 0, marginLeft: 8 }}>
                  {item.average_score.toFixed(1)} / 5 ({item.count} lượt)
                </Text>
              </div>
              <Progress
                percent={percent}
                strokeColor="#1890ff"
                showInfo={false}
                size="small"
              />
            </div>
          );
        })}
      </Card>

      {/* Feedback List */}
      <Card title="Ý kiến đóng góp & Nhận xét" size="small">
        <List
          itemLayout="horizontal"
          dataSource={summary.evaluations.filter((e) => Boolean(e.feedback_text))}
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
                      style={{ backgroundColor: item.is_anonymous ? '#8c8c8c' : '#1890ff' }}
                    />
                  }
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Text strong>{reviewerName}</Text>
                      {item.is_anonymous && <Tag color="default">Ẩn danh</Tag>}
                      <Tag color={isTrainerEval ? 'gold' : 'cyan'}>
                        {isTrainerEval ? 'Trainer -> Trainee' : 'Trainee -> Trainer'}
                      </Tag>
                      <Rate disabled value={item.average_score} style={{ fontSize: 12 }} />
                    </div>
                  }
                  description={
                    <Paragraph style={{ margin: '4px 0 0 0', color: '#595959' }}>
                      {item.feedback_text}
                    </Paragraph>
                  }
                />
              </List.Item>
            );
          }}
        />
      </Card>
    </div>
  );
};
