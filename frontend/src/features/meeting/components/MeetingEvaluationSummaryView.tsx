import React, { useEffect, useMemo, useState } from 'react';
import {
  Card,
  Progress,
  Rate,
  Typography,
  Spin,
  Empty,
  Tag,
  List,
  Avatar,
  Row,
  Col,
  Segmented,
} from 'antd';
import {
  StarFilled,
  UserOutlined,
  ReadOutlined,
  SmileOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import { meetingService } from '../services/meeting.service';
import type { MeetingEvaluationSummary, CriteriaBreakdown } from '../types/meeting.types';

const { Title, Text, Paragraph } = Typography;

interface Props {
  meetingId: number;
}

const CRITERIA_LABEL_MAP: Record<string, string> = {
  // Trainer to Trainee
  ATTENDANCE_CONDUCT: 'Chuyên cần & Tác phong',
  INTERACTION_CONTRIBUTION: 'Mức độ Tương tác & Đóng góp',
  ABSORPTION_COMPREHENSION: 'Mức độ Tiếp thu & Hiểu bài',
  PRE_CLASS_PREPARATION: 'Mức độ Chuẩn bị bài trước buổi học',
  TRAINER_TO_TRAINEE_ATTENDANCE: 'Chuyên cần & Tác phong',
  TRAINER_TO_TRAINEE_INTERACTION: 'Mức độ Tương tác & Đóng góp',
  TRAINER_TO_TRAINEE_COMPREHENSION: 'Mức độ Tiếp thu & Hiểu bài',
  TRAINER_TO_TRAINEE_PREPARATION: 'Mức độ Chuẩn bị bài trước buổi học',
  // Trainee to Trainer
  CONTENT_QUALITY: 'Chất lượng Nội dung bài học',
  TEACHING_METHOD: 'Phương pháp Giảng dạy & Hỗ trợ',
  CLASS_ATMOSPHERE: 'Không khí Lớp học & Sự tương tác',
  PRACTICAL_VALUE: 'Giá trị Thu nhận & Tính ứng dụng',
  TRAINEE_TO_TRAINER_CONTENT: 'Chất lượng Nội dung bài học',
  TRAINEE_TO_TRAINER_METHOD: 'Phương pháp Giảng dạy & Hỗ trợ',
  TRAINEE_TO_TRAINER_ATMOSPHERE: 'Không khí Lớp học & Sự tương tác',
  TRAINEE_TO_TRAINER_VALUE: 'Giá trị Thu nhận & Tính ứng dụng',
};

const TRAINER_TO_TRAINEE_CODES = new Set([
  'ATTENDANCE_CONDUCT',
  'INTERACTION_CONTRIBUTION',
  'ABSORPTION_COMPREHENSION',
  'PRE_CLASS_PREPARATION',
  'TRAINER_TO_TRAINEE_ATTENDANCE',
  'TRAINER_TO_TRAINEE_INTERACTION',
  'TRAINER_TO_TRAINEE_COMPREHENSION',
  'TRAINER_TO_TRAINEE_PREPARATION',
]);

const renderCriteriaList = (
  items: CriteriaBreakdown[],
  themeColor: string,
  emptyText: string
) => {
  if (items.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} style={{ margin: '16px 0' }} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {items.map((item) => {
        const label =
          item.criteria_name || CRITERIA_LABEL_MAP[item.criteria_code] || item.criteria_code;
        const percent = Math.round((item.average_score / 5) * 100);

        return (
          <div key={item.criteria_code}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                marginBottom: 4,
              }}
            >
              <div style={{ paddingRight: 8 }}>
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
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
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

export const MeetingEvaluationSummaryView: React.FC<Props> = ({ meetingId }) => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<MeetingEvaluationSummary | null>(null);
  const [feedbackFilter, setFeedbackFilter] = useState<'ALL' | 'TRAINER_TO_TRAINEE' | 'TRAINEE_TO_TRAINER'>('ALL');

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

  const {
    trainerCriteria,
    traineeCriteria,
    trainerAvgScore,
    traineeAvgScore,
    trainerCount,
    traineeCount,
    filteredFeedback,
  } = useMemo(() => {
    if (!summary) {
      return {
        trainerCriteria: [],
        traineeCriteria: [],
        trainerAvgScore: 0,
        traineeAvgScore: 0,
        trainerCount: 0,
        traineeCount: 0,
        filteredFeedback: [],
      };
    }

    const trainerList: CriteriaBreakdown[] = [];
    const traineeList: CriteriaBreakdown[] = [];

    summary.criteria_breakdown.forEach((item) => {
      if (item.evaluation_type === 'TRAINER_TO_TRAINEE' || TRAINER_TO_TRAINEE_CODES.has(item.criteria_code)) {
        trainerList.push(item);
      } else {
        traineeList.push(item);
      }
    });

    const trainerEvals = summary.evaluations.filter((e) => e.evaluation_type === 'TRAINER_TO_TRAINEE');
    const traineeEvals = summary.evaluations.filter((e) => e.evaluation_type === 'TRAINEE_TO_TRAINER');

    const trainerAvg =
      summary.trainer_average_score ??
      (trainerEvals.length > 0
        ? Number((trainerEvals.reduce((acc, curr) => acc + curr.average_score, 0) / trainerEvals.length).toFixed(1))
        : 0);

    const traineeAvg =
      summary.trainee_average_score ??
      (traineeEvals.length > 0
        ? Number((traineeEvals.reduce((acc, curr) => acc + curr.average_score, 0) / traineeEvals.length).toFixed(1))
        : 0);

    const feedbackList = summary.evaluations.filter((e) => Boolean(e.feedback_text));
    const filteredFb = feedbackList.filter((e) => {
      if (feedbackFilter === 'ALL') return true;
      return e.evaluation_type === feedbackFilter;
    });

    return {
      trainerCriteria: trainerList,
      traineeCriteria: traineeList,
      trainerAvgScore: trainerAvg,
      traineeAvgScore: traineeAvg,
      trainerCount: summary.total_trainer_evaluations ?? trainerEvals.length,
      traineeCount: summary.total_trainee_evaluations ?? traineeEvals.length,
      filteredFeedback: filteredFb,
    };
  }, [summary, feedbackFilter]);

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
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card style={{ height: '100%', backgroundColor: '#fafafa' }} size="small">
            <Text type="secondary" style={{ fontSize: 13 }}>Điểm Đánh Giá Chung</Text>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 4 }}>
              <Title level={2} style={{ margin: 0, color: '#faad14' }}>
                {summary.overall_average_score.toFixed(1)}
              </Title>
              <Text type="secondary" style={{ fontSize: 14 }}>/ 5.0</Text>
            </div>
            <Rate allowHalf disabled value={summary.overall_average_score} style={{ fontSize: 15, marginTop: 4 }} />
            <div style={{ marginTop: 8 }}>
              <Tag color="blue" style={{ fontSize: 12 }}>
                Tổng cộng: {summary.total_evaluations} phiếu
              </Tag>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card style={{ height: '100%', borderColor: '#ffd591', backgroundColor: '#fffbe6' }} size="small">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong style={{ color: '#d46b08' }}>
                <ReadOutlined style={{ marginRight: 6 }} /> Trainer đánh giá Trainee
              </Text>
              <Tag color="gold">{trainerCount} phiếu</Tag>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 8 }}>
              <Title level={3} style={{ margin: 0, color: '#d46b08' }}>
                {trainerCount > 0 ? trainerAvgScore.toFixed(1) : '--'}
              </Title>
              <Text type="secondary" style={{ fontSize: 13 }}>/ 5.0</Text>
            </div>
            <Rate allowHalf disabled value={trainerAvgScore} style={{ fontSize: 14, color: '#fa8c16', marginTop: 4 }} />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card style={{ height: '100%', borderColor: '#91d5ff', backgroundColor: '#e6f7ff' }} size="small">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong style={{ color: '#096dd9' }}>
                <SmileOutlined style={{ marginRight: 6 }} /> Trainee đánh giá Trainer
              </Text>
              <Tag color="blue">{traineeCount} phiếu</Tag>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 8 }}>
              <Title level={3} style={{ margin: 0, color: '#096dd9' }}>
                {traineeCount > 0 ? traineeAvgScore.toFixed(1) : '--'}
              </Title>
              <Text type="secondary" style={{ fontSize: 13 }}>/ 5.0</Text>
            </div>
            <Rate allowHalf disabled value={traineeAvgScore} style={{ fontSize: 14, color: '#1890ff', marginTop: 4 }} />
          </Card>
        </Col>
      </Row>

      {/* Criteria Breakdown - Tách 2 Bảng Trainer và Trainee */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 1. Trainer đánh giá Trainee */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
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
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
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

      {/* Feedback List */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
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
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Chưa có ý kiến nhận xét nào" style={{ margin: '16px 0' }} />
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
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
    </div>
  );
};

