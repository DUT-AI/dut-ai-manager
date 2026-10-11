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
    <div className="mb-4 sm:mb-6">
      <Row gutter={[8, 8]}>
        <Col xs={8} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100 rounded-xl text-center sm:text-left h-full">
            <Statistic
              title={<span className="text-[11px] sm:text-xs">Tổng thành viên</span>}
              value={totalParticipants}
              prefix={<TeamOutlined className="text-indigo-500 hidden sm:inline" />}
              suffix={<span className="text-[10px] sm:text-xs text-gray-400">học viên</span>}
              valueStyle={{ fontSize: '1.25rem', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={8} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100 rounded-xl text-center sm:text-left h-full">
            <Statistic
              title={<span className="text-[11px] sm:text-xs">Đã check-in</span>}
              value={checkedInCount}
              valueStyle={{ color: '#10b981', fontSize: '1.25rem', fontWeight: 600 }}
              prefix={<CheckCircleOutlined className="hidden sm:inline" />}
              suffix={<span className="text-[10px] sm:text-xs text-gray-400">/{totalParticipants}</span>}
            />
          </Card>
        </Col>
        <Col xs={8} sm={8}>
          <Card size="small" className="shadow-sm border-gray-100 rounded-xl text-center sm:text-left h-full">
            <Statistic
              title={<span className="text-[11px] sm:text-xs">Tỷ lệ tham gia</span>}
              value={participationRate}
              suffix="%"
              valueStyle={{ color: '#4f46e5', fontSize: '1.25rem', fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
