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
    <div className="p-3 sm:p-6 w-full max-w-7xl mx-auto space-y-4 sm:space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between gap-2">
        <Breadcrumb
          className="truncate text-xs sm:text-sm"
          items={[
            { title: <a onClick={() => navigate('/dashboard/meetings')}>Lịch Buổi Học</a> },
            { title: <span className="truncate max-w-[150px] sm:max-w-xs inline-block align-bottom">{meeting.title}</span> },
          ]}
        />
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard/meetings')}
          size="middle"
          className="shrink-0 text-xs sm:text-sm"
        >
          <span className="hidden sm:inline">Quay lại Lịch</span>
          <span className="sm:hidden">Lịch</span>
        </Button>
      </div>

      {/* Hero Header Card */}
      <MeetingHeroHeader meetingId={meetingId} />

      {/* Metrics Row */}
      <MeetingStatsRow meetingId={meetingId} />

      {/* Main Content Tabs */}
      <Card className="shadow-sm border-gray-100 rounded-xl" bodyStyle={{ padding: '12px 16px' }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          className="meeting-detail-tabs"
          items={[
            {
              key: 'participants',
              label: (
                <span className="flex items-center gap-1.5 text-xs sm:text-sm">
                  <TeamOutlined />
                  Tham gia ({totalParticipants})
                </span>
              ),
              children: <MeetingParticipantsTab meetingId={meetingId} />,
            },
            ...(meeting.enable_evaluation
              ? [
                  {
                    key: 'evaluations',
                    label: (
                      <span className="flex items-center gap-1.5 text-xs sm:text-sm">
                        <BarChartOutlined />
                        Báo cáo Đánh giá
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
