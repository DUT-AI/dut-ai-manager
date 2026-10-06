import React, { useState, useMemo } from 'react';
import { Table, Avatar, Tag, Typography, Image, Button, Space, Progress, Segmented, Card, Alert, Tooltip } from 'antd';
import {
  UserOutlined,
  StarOutlined,
  StarFilled,
  CheckCircleOutlined,
  TrophyOutlined,
  HeartFilled,
  HeartOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ParticipantResponse, UpdateParticipantStatusPayload, EvaluationResponse } from '../types/meeting.types';
import { ParticipantStatus } from '../types/meeting.types';
import { useMeetingDetail, useUpdateParticipantStatus, useMeetingEvaluationSummary } from '../hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { ParticipantStatusTag } from './ParticipantStatusTag';
import { ParticipantActionButtons } from './ParticipantActionButtons';
import { MeetingBatchCheckInBanner } from './MeetingBatchCheckInBanner';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';
import { TrainerEvaluationModal } from './TrainerEvaluationModal';
import { TraineeEvaluationModal } from './TraineeEvaluationModal';
import { MyEvaluationResultModal } from './MyEvaluationResultModal';

const { Text } = Typography;

interface Props {
  meetingId: number;
}

export const MeetingParticipantsTab: React.FC<Props> = ({ meetingId }) => {
  const { data: meeting, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();

  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [isEditStatusModalOpen, setIsEditStatusModalOpen] = useState(false);
  const [evaluatingParticipant, setEvaluatingParticipant] = useState<ParticipantResponse | null>(null);
  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);
  const [evalFilter, setEvalFilter] = useState<'all' | 'unrated' | 'rated'>('all');

  const updateParticipantStatusMutation = useUpdateParticipantStatus();
  const { data: evalSummary, refetch: refetchEvalSummary } = useMeetingEvaluationSummary(
    meetingId,
    Boolean(meeting?.enable_evaluation)
  );

  const currentUserId = user?.id;
  const isTrainer =
    (meeting?.created_by ? currentUserId === meeting.created_by : false) ||
    (meeting?.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);

  const isEnded = meeting ? dayjs().isAfter(dayjs(meeting.end_time)) : false;
  const totalParticipants = meeting?.participants?.length || 0;

  // Build evaluation maps
  const {
    trainerEvalsByTraineeId,
    traineeEvalsByReviewerId,
    myEvalForTrainer,
    isCurrentUserTrainee,
    trainees,
    trainerEvaluatedCount,
    traineeEvaluatedCount,
  } = useMemo(() => {
    const trainerMap = new Map<number, EvaluationResponse>();
    const traineeMap = new Map<number, EvaluationResponse>();

    if (evalSummary?.evaluations) {
      evalSummary.evaluations.forEach((e) => {
        if (e.evaluation_type === 'TRAINER_TO_TRAINEE') {
          trainerMap.set(e.target_user_id, e);
        } else if (e.evaluation_type === 'TRAINEE_TO_TRAINER' && e.reviewer_id) {
          traineeMap.set(e.reviewer_id, e);
        }
      });
    }

    const allTrainees = (meeting?.participants || []).filter(
      (p) => p.user_id !== meeting?.created_by && p.user_id !== meeting?.trainer?.id
    );

    const activeTrainees = allTrainees.filter(
      (p) =>
        p.status !== ParticipantStatus.ABSENT_EXCUSED &&
        p.status !== ParticipantStatus.ABSENT_UNEXCUSED
    );

    const trainerCount = activeTrainees.filter((p) => trainerMap.has(p.user_id)).length;
    const traineeCount = activeTrainees.filter((p) => traineeMap.has(p.user_id)).length;

    const myEval = currentUserId ? traineeMap.get(currentUserId) : null;
    const isTrainee = allTrainees.some((p) => p.user_id === currentUserId);

    return {
      trainerEvalsByTraineeId: trainerMap,
      traineeEvalsByReviewerId: traineeMap,
      myEvalForTrainer: myEval,
      isCurrentUserTrainee: isTrainee,
      trainees: activeTrainees,
      trainerEvaluatedCount: trainerCount,
      traineeEvaluatedCount: traineeCount,
    };
  }, [evalSummary, meeting, currentUserId]);

  if (!meeting) return null;

  const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
    if (!editingParticipant) return;
    await updateParticipantStatusMutation.mutateAsync({
      meetingId: meeting.id,
      userId: editingParticipant.user_id,
      payload,
    });
    refetch();
  };

  // Filter participants based on evaluation filter
  const filteredParticipants = (meeting.participants || []).filter((p) => {
    if (!meeting.enable_evaluation || evalFilter === 'all') return true;
    const isEvaluated = trainerEvalsByTraineeId.has(p.user_id);
    if (evalFilter === 'rated') return isEvaluated;
    if (evalFilter === 'unrated') {
      const isAbsent =
        p.status === ParticipantStatus.ABSENT_EXCUSED ||
        p.status === ParticipantStatus.ABSENT_UNEXCUSED;
      const isMeetingCreator = p.user_id === meeting.created_by;
      return !isEvaluated && !isAbsent && !isMeetingCreator;
    }
    return true;
  });

  const columns = [
    {
      title: 'Thành viên',
      key: 'user',
      render: (_: unknown, record: ParticipantResponse) => (
        <div className="flex items-center gap-3">
          <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="default" />
          <div>
            <Text strong className="block text-sm">
              {record.user_name || `User #${record.user_id}`}
            </Text>
            {record.user_id === meeting.created_by && (
              <Tag color="gold" className="text-[10px] m-0">
                Trainer / Tạo buổi
              </Tag>
            )}
          </div>
        </div>
      ),
      sorter: (a: ParticipantResponse, b: ParticipantResponse) =>
        (a.user_name || '').localeCompare(b.user_name || ''),
    },
    {
      title: 'Trạng thái tham gia',
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => <ParticipantStatusTag status={status} />,
      sorter: (a: ParticipantResponse, b: ParticipantResponse) =>
        (a.status || '').localeCompare(b.status || ''),
    },
    {
      title: 'Check-in',
      dataIndex: 'check_in_at',
      key: 'check_in_at',
      render: (text: string) => (text ? dayjs(text).format('HH:mm:ss') : '—'),
      sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
        if (!a.check_in_at) return 1;
        if (!b.check_in_at) return -1;
        return dayjs(a.check_in_at).unix() - dayjs(b.check_in_at).unix();
      },
    },
    {
      title: 'Check-out',
      dataIndex: 'check_out_at',
      key: 'check_out_at',
      render: (text: string, record: ParticipantResponse) => {
        if (text) return dayjs(text).format('HH:mm:ss');
        if (isEnded && record.check_in_at) {
          return `${dayjs(meeting.end_time).format('HH:mm')} (Tự động)`;
        }
        return '—';
      },
      sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
        const aTime = a.check_out_at || (isEnded && a.check_in_at ? meeting.end_time : null);
        const bTime = b.check_out_at || (isEnded && b.check_in_at ? meeting.end_time : null);
        if (!aTime) return 1;
        if (!bTime) return -1;
        return dayjs(aTime).unix() - dayjs(bTime).unix();
      },
    },
    ...(meeting.enable_evaluation
      ? [
          {
            title: 'Đánh giá Trainer',
            key: 'trainee_eval',
            render: (_: unknown, record: ParticipantResponse) => {
              if (record.user_id === meeting.created_by) {
                return <Text type="secondary" className="text-xs">—</Text>;
              }
              const existing = traineeEvalsByReviewerId.get(record.user_id);
              if (existing) {
                return (
                  <Tag color="blue" icon={<CheckCircleOutlined />} className="text-xs py-0.5 px-2">
                    Đã gửi {record.user_id === currentUserId ? `(⭐ ${existing.average_score.toFixed(1)})` : ''}
                  </Tag>
                );
              }
              return <Tag color="default" className="text-xs py-0.5 px-2">Chưa gửi</Tag>;
            },
          },
        ]
      : []),
    {
      title: 'Ảnh quẹt thẻ',
      dataIndex: 'link_image',
      key: 'link_image',
      render: (url: string) =>
        url ? (
          <Image
            src={url}
            alt="Checkin"
            width={44}
            height={44}
            className="rounded-lg object-cover cursor-pointer hover:opacity-85 shadow-sm border border-gray-100"
            preview={{
              mask: <div className="text-[11px]">Xem ảnh</div>,
            }}
          />
        ) : (
          <Text type="secondary" className="text-xs">
            —
          </Text>
        ),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_: unknown, record: ParticipantResponse) => (
        <ParticipantActionButtons
          meetingId={meetingId}
          record={record}
          isTrainer={isTrainer}
          isEnded={isEnded}
          enableEvaluation={meeting.enable_evaluation}
          existingEvaluation={trainerEvalsByTraineeId.get(record.user_id)}
          onEditStatus={(p) => {
            setEditingParticipant(p);
            setIsEditStatusModalOpen(true);
          }}
          onEvaluate={(p) => setEvaluatingParticipant(p)}
        />
      ),
    },
  ];

  const totalActiveTrainees = trainees.length;
  const trainerEvalPercent = totalActiveTrainees > 0 ? Math.round((trainerEvaluatedCount / totalActiveTrainees) * 100) : 0;
  const traineeEvalPercent = totalActiveTrainees > 0 ? Math.round((traineeEvaluatedCount / totalActiveTrainees) * 100) : 0;
  const unratedCount = Math.max(0, totalActiveTrainees - trainerEvaluatedCount);

  return (
    <div className="space-y-4">
      {/* Batch Check-in Banner if unjoined participants exist */}
      <MeetingBatchCheckInBanner meetingId={meetingId} />

      {/* Trainee Self-Evaluation Banner & Quick Access */}
      {meeting.enable_evaluation && isCurrentUserTrainee && (
        <Card size="small" className="border-indigo-100 bg-gradient-to-r from-indigo-50/70 to-blue-50/50 shadow-sm rounded-xl">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
                {myEvalForTrainer ? <HeartFilled className="text-lg text-pink-500" /> : <HeartOutlined className="text-lg text-indigo-500" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <Text strong className="text-indigo-950 text-sm">
                    Đánh giá Giảng viên (Trainer) của bạn
                  </Text>
                  {myEvalForTrainer ? (
                    <Tag color="success" className="text-xs m-0">
                      ✓ Đã hoàn thành (⭐ {myEvalForTrainer.average_score.toFixed(1)}/5)
                    </Tag>
                  ) : (
                    <Tag color="warning" className="text-xs m-0">
                      Chưa đánh giá
                    </Tag>
                  )}
                </div>
                <Text type="secondary" className="text-xs text-indigo-700 block mt-0.5">
                  {myEvalForTrainer
                    ? 'Bạn đã gửi đánh giá cho Trainer. Bạn có thể mở khóa xem bảng điểm rèn luyện cá nhân!'
                    : 'Hãy gửi đánh giá & nhận xét cho Trainer để mở khóa xem điểm rèn luyện cá nhân của bạn.'}
                </Text>
              </div>
            </div>
            <Space wrap className="shrink-0">
              <Button
                icon={<TrophyOutlined className="text-yellow-600" />}
                onClick={() => setIsMyResultOpen(true)}
                className="bg-white border-indigo-200 text-indigo-800 hover:!border-indigo-400"
                size="small"
              >
                Xem Điểm của tôi
              </Button>
              <Button
                type="primary"
                icon={<StarFilled />}
                onClick={() => setIsTraineeEvalOpen(true)}
                className={myEvalForTrainer ? 'bg-indigo-600 hover:!bg-indigo-500' : 'bg-amber-600 hover:!bg-amber-500'}
                size="small"
              >
                {myEvalForTrainer ? 'Sửa đánh giá Trainer' : 'Đánh giá Trainer ngay'}
              </Button>
            </Space>
          </div>
        </Card>
      )}

      {/* Evaluation Progress & Filter Bar */}
      {meeting.enable_evaluation && (
        <Card size="small" className="bg-gray-50/80 border-gray-200/80 shadow-none rounded-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Progress Bars */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-6 flex-1">
              <div className="flex-1">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-medium text-gray-700">
                    👨‍🏫 Trainer đánh giá Học viên:
                  </span>
                  <span className="font-semibold text-emerald-700">
                    {trainerEvaluatedCount} / {totalActiveTrainees} ({trainerEvalPercent}%)
                  </span>
                </div>
                <Progress
                  percent={trainerEvalPercent}
                  size="small"
                  strokeColor="#10b981"
                  showInfo={false}
                />
              </div>

              <div className="flex-1">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-medium text-gray-700">
                    🎓 Học viên đánh giá Trainer:
                  </span>
                  <span className="font-semibold text-blue-700">
                    {traineeEvaluatedCount} / {totalActiveTrainees} ({traineeEvalPercent}%)
                  </span>
                </div>
                <Progress
                  percent={traineeEvalPercent}
                  size="small"
                  strokeColor="#3b82f6"
                  showInfo={false}
                />
              </div>
            </div>

            {/* Filter */}
            <div className="flex items-center gap-2 shrink-0">
              <Text type="secondary" className="text-xs">Lọc danh sách:</Text>
              <Segmented
                size="small"
                value={evalFilter}
                onChange={(val) => setEvalFilter(val as any)}
                options={[
                  { label: `Tất cả (${totalParticipants})`, value: 'all' },
                  { label: `Chưa đánh giá (${unratedCount})`, value: 'unrated' },
                  { label: `Đã đánh giá (${trainerEvaluatedCount})`, value: 'rated' },
                ]}
              />
            </div>
          </div>
        </Card>
      )}

      {/* Participants Table */}
      <Table
        dataSource={filteredParticipants}
        columns={columns}
        rowKey="user_id"
        pagination={filteredParticipants.length > 10 ? { pageSize: 10 } : false}
        className="mt-2 shadow-sm rounded-lg overflow-hidden border border-gray-100"
      />

      {/* Edit Attendance Status Modal */}
      <EditParticipantStatusModal
        open={isEditStatusModalOpen}
        participant={editingParticipant}
        onClose={() => {
          setIsEditStatusModalOpen(false);
          setEditingParticipant(null);
        }}
        onSubmit={handleUpdateStatus}
        loading={updateParticipantStatusMutation.isPending}
      />

      {/* Trainer Evaluation Modal */}
      {evaluatingParticipant && (
        <TrainerEvaluationModal
          open={!!evaluatingParticipant}
          meetingId={meeting.id}
          trainee={evaluatingParticipant}
          existingEvaluation={trainerEvalsByTraineeId.get(evaluatingParticipant.user_id)}
          participants={meeting.participants}
          onSelectTrainee={(p) => setEvaluatingParticipant(p)}
          onSuccess={() => {
            setEvaluatingParticipant(null);
            refetch();
            refetchEvalSummary();
          }}
          onClose={() => setEvaluatingParticipant(null)}
          onCancel={() => setEvaluatingParticipant(null)}
        />
      )}

      {/* Trainee Evaluation Modal */}
      <TraineeEvaluationModal
        open={isTraineeEvalOpen}
        meetingId={meeting.id}
        trainerId={meeting.trainer?.id || meeting.created_by || undefined}
        trainerName={meeting.trainer?.name}
        trainerAvatarUrl={meeting.trainer?.avatar_url}
        existingEvaluation={myEvalForTrainer}
        onSuccess={() => {
          setIsTraineeEvalOpen(false);
          refetch();
          refetchEvalSummary();
        }}
        onClose={() => setIsTraineeEvalOpen(false)}
        onCancel={() => setIsTraineeEvalOpen(false)}
      />

      {/* My Evaluation Result Modal */}
      <MyEvaluationResultModal
        open={isMyResultOpen}
        meetingId={meeting.id}
        onClose={() => setIsMyResultOpen(false)}
      />
    </div>
  );
};

