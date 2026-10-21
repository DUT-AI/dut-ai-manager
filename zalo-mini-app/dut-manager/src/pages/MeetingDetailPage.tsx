import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Page, Icon, Button } from 'zmp-ui';
import Header from '@/components/Header';
import PageLoading from '@/components/PageLoading';
import { useAuth } from '@/context/AuthContext';
import { meetingService } from '@/services/api/meeting.service';
import type {
  MeetingDetailResponse,
  ParticipantResponse,
  MeetingOverallEvaluationResponse,
  EvaluationResponse,
  MeetingEvaluationSummary,
} from '@/types/meeting.types';
import { MeetingHeroCard } from '@/features/schedule/MeetingHeroCard';
import { MeetingStatsCard } from '@/features/schedule/MeetingStatsCard';
import { MeetingParticipantsTab } from '@/features/schedule/MeetingParticipantsTab';
import { MeetingEvaluationTab } from '@/features/schedule/MeetingEvaluationTab';
import { EditParticipantStatusModal } from '@/features/schedule/EditParticipantStatusModal';

const MeetingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const meetingId = Number(id);
  const { user, hasPermission } = useAuth();

  const [meeting, setMeeting] = useState<MeetingDetailResponse | null>(null);
  const [overallEvaluation, setOverallEvaluation] = useState<MeetingOverallEvaluationResponse | null>(null);
  const [evaluationSummary, setEvaluationSummary] = useState<MeetingEvaluationSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [activeTab, setActiveTab] = useState<string>('participants');

  const hasUpdatePermission = hasPermission('meetings:update');

  const fetchMeeting = async () => {
    if (!meetingId) return;
    setIsLoading(true);
    try {
      const [meetingData, evalSummaryRes, overallEvalRes] = await Promise.all([
        meetingService.getMeetingById(meetingId),
        meetingService.getMeetingEvaluationSummary(meetingId).catch(() => null),
        meetingService.getMeetingOverallEvaluation(meetingId).catch(() => null),
      ]);

      setMeeting(meetingData);
      if (evalSummaryRes?.data) {
        setEvaluationSummary(evalSummaryRes.data);
      }
      if (overallEvalRes?.data) {
        setOverallEvaluation(overallEvalRes.data);
      }
    } catch (err) {
      console.error('Failed to load meeting details', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMeeting();
  }, [meetingId]);

  if (isLoading) {
    return <PageLoading text="Đang tải thông tin buổi học..." />;
  }

  if (!meeting) {
    return (
      <Page className="bg-[#f8fafc] flex flex-col min-h-screen">
        <Header title="Chi tiết Buổi sinh hoạt" showBack={true} />
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mb-3">
            <Icon icon="zi-warning-circle" size={28} />
          </div>
          <h3 className="font-bold text-base text-gray-800">Không tìm thấy buổi học</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-xs">
            Buổi học này không tồn tại hoặc bạn chưa được cấp quyền truy cập.
          </p>
          <Button
            className="mt-4 rounded-xl bg-blue-600 text-white font-bold text-xs"
            onClick={() => navigate(-1)}
          >
            Quay lại
          </Button>
        </div>
      </Page>
    );
  }

  const isTrainer =
    user?.id !== undefined &&
    (meeting.trainer?.id === user.id || meeting.created_by === user.id);

  // Tìm đánh giá cá nhân của Trainee gửi cho Trainer nếu có
  const myEvalForTrainer =
    evaluationSummary?.evaluations?.find(
      (e) => e.reviewer_id === user?.id && e.evaluation_type === 'TRAINEE_TO_TRAINER'
    ) || evaluationSummary?.my_evaluation || null;

  return (
    <Page className="bg-[#f8fafc] flex flex-col min-h-screen">
      <Header title="Chi tiết Buổi học" showBack={true} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-3 pb-24 overflow-y-auto">
        {/* 1. Hero Card */}
        <MeetingHeroCard meeting={meeting} />

        {/* 2. Attendance Stats */}
        <MeetingStatsCard participants={meeting.participants} />

        {/* 3. Main Tabs Navigation */}
        <div className="bg-white rounded-2xl p-2 border border-gray-100 shadow-sm">
          <div className="flex bg-gray-100 p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('participants')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'participants'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Tham gia ({meeting.participants.length})
            </button>

            {meeting.enable_evaluation && (
              <button
                onClick={() => setActiveTab('evaluation')}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'evaluation'
                    ? 'bg-white text-blue-600 shadow-xs'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Đánh giá buổi học
              </button>
            )}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'participants' ? (
          <MeetingParticipantsTab
            meetingId={meeting.id}
            participants={meeting.participants}
            currentUserId={user?.id}
            hasUpdatePermission={hasUpdatePermission}
            onEditParticipantStatus={(p) => setEditingParticipant(p)}
            onRefetch={fetchMeeting}
          />
        ) : (
          <MeetingEvaluationTab
            meeting={meeting}
            currentUserId={user?.id}
            isTrainer={isTrainer}
            hasUpdatePermission={hasUpdatePermission}
            overallEvaluation={overallEvaluation || evaluationSummary?.overall_evaluation}
            myEvalForTrainer={myEvalForTrainer}
            evaluationSummary={evaluationSummary}
            onRefetch={fetchMeeting}
          />
        )}
      </div>

      {/* Host Edit Participant Status Modal */}
      <EditParticipantStatusModal
        meetingId={meeting.id}
        participant={editingParticipant}
        onClose={() => setEditingParticipant(null)}
        onSuccess={fetchMeeting}
      />
    </Page>
  );
};

export default MeetingDetailPage;
