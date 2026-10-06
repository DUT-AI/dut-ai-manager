import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { TeamOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useMeetingDetail } from '../hooks/useMeetings';
import { ParticipantStatus } from '../types/meeting.types';

interface Props {
  meetingId: number;
}

export const MeetingStatsRow: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting } = useMeetingDetail(meetingId);

  if (!meeting) return null;

  const totalParticipants = meeting.participants.length;
  const checkedInCount = meeting.participants.filter(
    (p) =>
      p.status === ParticipantStatus.JOINED ||
      p.status === ParticipantStatus.LATE_EXCUSED ||
      p.status === ParticipantStatus.LATE_UNEXCUSED ||
      p.status === ParticipantStatus.COMPLETED
  ).length;

  const participationRate =
    totalParticipants > 0 ? Math.round((checkedInCount / totalParticipants) * 100) : 0;

  return (
    <div style={{ marginBottom: 24 }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100">
            <Statistic
              title="Tổng số thành viên"
              value={totalParticipants}
              prefix={<TeamOutlined className="text-indigo-500" />}
              suffix="học viên"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100">
            <Statistic
              title="Đã check-in"
              value={checkedInCount}
              valueStyle={{ color: '#10b981' }}
              prefix={<CheckCircleOutlined />}
              suffix={`/ ${totalParticipants}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100">
            <Statistic
              title="Tỷ lệ tham gia"
              value={participationRate}
              suffix="%"
              valueStyle={{ color: '#4f46e5' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
