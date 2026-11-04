import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Tabs, Spin, Alert, Breadcrumb } from 'antd';
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useMeetingDetail, useMeetingOverallEvaluation } from '@/features/meeting/hooks/useMeetings';
import { useMeetingEvents } from '@/features/meeting/hooks/useMeetingEvents';
import {
  MeetingHeroHeader,
  MeetingStatsRow,
  MeetingParticipantsTab,
  MeetingEvaluationSummaryView,
  TraineeEvaluationModal,
  MeetingOverallEvaluationModal,
} from '../components';

export const MeetingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const meetingId = Number(id);

  const { data: meeting, isLoading, error, refetch } = useMeetingDetail(meetingId);
  const { data: overallEval, refetch: refetchOverallEval } = useMeetingOverallEvaluation(meetingId);
  const [activeTab, setActiveTab] = useState('participants');
  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isOverallEvalOpen, setIsOverallEvalOpen] = useState(false);

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

  const totalParticipants = (meeting.trainers?.length || 0) + (meeting.trainees?.length || 0);

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
              children: (
                <MeetingParticipantsTab
                  meetingId={meetingId}
                  onOpenTraineeEvaluation={() => setIsTraineeEvalOpen(true)}
                  onOpenOverallEvaluation={() => setIsOverallEvalOpen(true)}
                  overallEval={overallEval}
                />
              ),
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

      {/* Single-Modal Instances (Mounted once at Page level) */}
      <TraineeEvaluationModal
        open={isTraineeEvalOpen}
        meetingId={meetingId}
        trainers={meeting.trainers || []}
        onSuccess={() => {
          setIsTraineeEvalOpen(false);
          refetch();
        }}
        onClose={() => setIsTraineeEvalOpen(false)}
      />

      <MeetingOverallEvaluationModal
        open={isOverallEvalOpen}
        meetingId={meetingId}
        meetingTitle={meeting.title}
        existingEvaluation={overallEval}
        onSuccess={() => {
          setIsOverallEvalOpen(false);
          refetch();
          refetchOverallEval();
        }}
        onClose={() => setIsOverallEvalOpen(false)}
        onCancel={() => setIsOverallEvalOpen(false)}
      />
    </div>
  );
};

export default MeetingDetailPage;
