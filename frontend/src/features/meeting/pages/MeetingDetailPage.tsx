import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Tabs, Spin, Alert, Breadcrumb } from 'antd';
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useMeetingDetail } from '@/features/meeting/hooks/useMeetings';
import { useMeetingEvents } from '@/features/meeting/hooks/useMeetingEvents';
import {
  MeetingHeroHeader,
  MeetingStatsRow,
  MeetingParticipantsTab,
  MeetingEvaluationSummaryView,
} from '../components';

export const MeetingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const meetingId = Number(id);

  const { data: meeting, isLoading, error } = useMeetingDetail(meetingId);
  const [activeTab, setActiveTab] = useState('participants');

  // SSE Events listener
  useMeetingEvents(meetingId, true);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spin size="large" tip="Đang tải thông tin buổi học..." />
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="p-6">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard/meetings')} className="mb-4">
          Quay lại Lịch
        </Button>
        <Alert
          type="error"
          showIcon
          message="Không tìm thấy buổi học"
          description="Buổi học này không tồn tại hoặc đã bị xóa."
        />
      </div>
    );
  }

  const totalParticipants = meeting.participants.length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Breadcrumb
          items={[
            { title: <a onClick={() => navigate('/dashboard/meetings')}>Lịch Buổi Học</a> },
            { title: meeting.title },
          ]}
        />
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard/meetings')}>
          Quay lại Lịch
        </Button>
      </div>

      {/* Hero Header Card */}
      <MeetingHeroHeader meetingId={meetingId} />


      {/* Metrics Row */}
      <MeetingStatsRow meetingId={meetingId} />

      {/* Main Content Tabs */}
      <Card className="shadow-sm border-gray-100">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
          items={[
            {
              key: 'participants',
              label: (
                <span className="flex items-center gap-2">
                  <TeamOutlined />
                  Danh sách tham gia ({totalParticipants})
                </span>
              ),
              children: <MeetingParticipantsTab meetingId={meetingId} />,
            },
            ...(meeting.enable_evaluation
              ? [
                  {
                    key: 'evaluations',
                    label: (
                      <span className="flex items-center gap-2">
                        <BarChartOutlined />
                        Báo cáo Đánh giá Buổi học
                      </span>
                    ),
                    children: (
                      <div className="py-2">
                        <MeetingEvaluationSummaryView meetingId={meeting.id} />
                      </div>
                    ),
                  },
                ]
              : []),
          ]}
        />
      </Card>
    </div>
  );
};

export default MeetingDetailPage;
