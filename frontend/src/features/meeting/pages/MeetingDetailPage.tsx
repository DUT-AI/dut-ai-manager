import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Avatar,
  Tag,
  Typography,
  Descriptions,
  Button,
  Popconfirm,
  Image,
  Tooltip,
  Tabs,
  Spin,
  Alert,
  Breadcrumb,
  Space,
  Row,
  Col,
  Statistic,
  message,
} from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  SafetyCertificateOutlined,
  StarOutlined,
  TrophyOutlined,
  BarChartOutlined,
  TeamOutlined,
  CalendarOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ParticipantResponse, UpdateParticipantStatusPayload } from '@/features/meeting/types/meeting.types';
import { ParticipantStatus } from '@/features/meeting/types/meeting.types';
import { useMeetingDetail, useUpdateParticipantStatus, useDeleteMeeting, useUpdateMeeting } from '@/features/meeting/hooks/useMeetings';
import { useMeetingEvents } from '@/features/meeting/hooks/useMeetingEvents';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useUsers } from '@/features/users/hooks/useUsers';
import { EditParticipantStatusModal } from '../components/EditParticipantStatusModal';
import { TrainerEvaluationModal } from '../components/TrainerEvaluationModal';
import { TraineeEvaluationModal } from '../components/TraineeEvaluationModal';
import { MeetingEvaluationSummaryView } from '../components/MeetingEvaluationSummaryView';
import { MyEvaluationResultModal } from '../components/MyEvaluationResultModal';
import { MeetingModal } from '../components/MeetingModal';

const { Title, Text, Paragraph } = Typography;

export const MeetingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const meetingId = Number(id);

  const { data: meeting, isLoading, error, refetch } = useMeetingDetail(meetingId);
  const { user } = useAuth();
  const { data: users = [] } = useUsers();

  const [activeTab, setActiveTab] = useState('participants');
  const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
  const [isEditStatusModalOpen, setIsEditStatusModalOpen] = useState(false);
  const [isEditMeetingModalOpen, setIsEditMeetingModalOpen] = useState(false);

  // Evaluation modal states
  const [evaluatingParticipant, setEvaluatingParticipant] = useState<ParticipantResponse | null>(null);
  const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
  const [isMyResultOpen, setIsMyResultOpen] = useState(false);

  // Mutations
  const updateParticipantStatusMutation = useUpdateParticipantStatus();
  const deleteMeetingMutation = useDeleteMeeting();
  const updateMeetingMutation = useUpdateMeeting();

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

  const currentUserId = user?.id;
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader'].includes(r.toLowerCase())) ?? false);
  const myParticipantRecord = meeting.participants.find((p) => p.user_id === currentUserId);
  const isTrainee = !!myParticipantRecord;

  const checkedInCount = meeting.participants.filter(
    (p) =>
      p.status === ParticipantStatus.JOINED ||
      p.status === ParticipantStatus.LATE_EXCUSED ||
      p.status === ParticipantStatus.LATE_UNEXCUSED ||
      p.status === ParticipantStatus.COMPLETED
  ).length;
  const totalParticipants = meeting.participants.length;
  const isOngoing = dayjs().isAfter(dayjs(meeting.start_time)) && dayjs().isBefore(dayjs(meeting.end_time));
  const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

  const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
    if (!editingParticipant) return;
    await updateParticipantStatusMutation.mutateAsync({
      meetingId: meeting.id,
      userId: editingParticipant.user_id,
      payload,
    });
    refetch();
  };

  const handleDeleteMeeting = async () => {
    try {
      await deleteMeetingMutation.mutateAsync(meeting.id);
      message.success('Đã xóa buổi học thành công');
      navigate('/dashboard/meetings');
    } catch {
      message.error('Không thể xóa buổi học');
    }
  };

  const handleEditMeetingSubmit = async (data: any) => {
    try {
      await updateMeetingMutation.mutateAsync({ id: meeting.id, data });
      message.success('Cập nhật buổi học thành công');
      setIsEditMeetingModalOpen(false);
      refetch();
    } catch {
      message.error('Không thể cập nhật buổi học');
    }
  };

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
      render: (status: ParticipantStatus) => {
        let tagColor = 'default';
        let tagIcon = <CloseCircleOutlined />;
        let tagText = 'Chưa checkin';

        switch (status) {
          case ParticipantStatus.JOINED:
            tagColor = 'green';
            tagIcon = <CheckCircleOutlined />;
            tagText = 'Đã checkin';
            break;
          case ParticipantStatus.LATE_EXCUSED:
            tagColor = 'blue';
            tagIcon = <ClockCircleOutlined />;
            tagText = 'Trễ (Có phép)';
            break;
          case ParticipantStatus.LATE_UNEXCUSED:
            tagColor = 'orange';
            tagIcon = <ClockCircleOutlined />;
            tagText = 'Trễ (Không phép)';
            break;
          case ParticipantStatus.ABSENT_EXCUSED:
            tagColor = 'purple';
            tagIcon = <CloseCircleOutlined />;
            tagText = 'Vắng (Có phép)';
            break;
          case ParticipantStatus.ABSENT_UNEXCUSED:
            tagColor = 'red';
            tagIcon = <CloseCircleOutlined />;
            tagText = 'Vắng (Không phép)';
            break;
          case ParticipantStatus.COMPLETED:
            tagColor = 'cyan';
            tagIcon = <CheckCircleOutlined />;
            tagText = 'Hoàn thành';
            break;
          case ParticipantStatus.NOT_JOINED:
          default:
            tagColor = 'default';
            tagIcon = <CloseCircleOutlined />;
            tagText = 'Chưa checkin';
            break;
        }

        return (
          <Tag color={tagColor} icon={tagIcon} className="px-2.5 py-0.5 text-xs font-medium">
            {tagText}
          </Tag>
        );
      },
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
    {
      title: 'Ảnh quẹt thẻ / Checkin',
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
        <Space size="small">
          {meeting.enable_evaluation && isTrainer && isEnded && (
            <Tooltip title="Chấm điểm đánh giá học viên này">
              <Button
                icon={<StarOutlined className="text-amber-500" />}
                size="small"
                type="dashed"
                className="hover:!border-amber-400"
                onClick={() => setEvaluatingParticipant(record)}
              >
                Đánh giá
              </Button>
            </Tooltip>
          )}
          {isTrainer && (
            <Tooltip title="Chỉnh sửa trạng thái điểm danh">
              <Button
                icon={<EditOutlined />}
                size="small"
                onClick={() => {
                  setEditingParticipant(record);
                  setIsEditStatusModalOpen(true);
                }}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

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
      <div
        className="rounded-2xl p-6 text-white shadow-lg relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        }}
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Title level={3} className="!text-white !mb-0">
                {meeting.title}
              </Title>
              {isOngoing && <Tag color="processing" className="!bg-emerald-500/20 !text-emerald-200 border-none">Đang diễn ra</Tag>}
              {isEnded && <Tag color="default" className="!bg-white/20 !text-white border-none">Đã kết thúc</Tag>}
              {meeting.enable_evaluation && (
                <Tag color="warning" className="!bg-amber-500/20 !text-amber-200 border-none">
                  Đánh giá 2 chiều (Hạn 24h)
                </Tag>
              )}
            </div>

            <div className="flex items-center gap-4 text-white/80 text-sm flex-wrap">
              <span className="flex items-center gap-1.5">
                <CalendarOutlined />
                {dayjs(meeting.start_time).format('dddd, DD/MM/YYYY')}
              </span>
              <span className="flex items-center gap-1.5">
                <ClockCircleOutlined />
                {dayjs(meeting.start_time).format('HH:mm')} - {dayjs(meeting.end_time).format('HH:mm')}
              </span>
              {meeting.require_check_in && (
                <span className="flex items-center gap-1.5 text-emerald-200">
                  <SafetyCertificateOutlined />
                  Bắt buộc check-in
                </span>
              )}
            </div>

            {meeting.content && (
              <Paragraph className="!text-white/90 !mb-0 text-sm pt-2 max-w-3xl">
                {meeting.content}
              </Paragraph>
            )}
          </div>

          {/* Action buttons on header */}
          {isTrainer && (
            <div className="flex items-center gap-2 self-start md:self-center shrink-0">
              <Button
                ghost
                icon={<EditOutlined />}
                onClick={() => setIsEditMeetingModalOpen(true)}
              >
                Chỉnh sửa
              </Button>
              <Popconfirm
                title="Xác nhận xóa buổi học?"
                description="Bạn có chắc chắn muốn xóa buổi học này không?"
                onConfirm={handleDeleteMeeting}
                okText="Xóa"
                cancelText="Hủy"
              >
                <Button danger type="primary" icon={<DeleteOutlined />}>
                  Xóa
                </Button>
              </Popconfirm>
            </div>
          )}
        </div>
      </div>

      {/* Trainee Action Banner if Evaluation is Enabled */}
      {meeting.enable_evaluation && isTrainee && isEnded && (
        <div style={{ marginBottom: 24 }}>
          <Card className="border-amber-200 bg-amber-50/50 shadow-sm" style={{ width: '100%' }}>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <StarOutlined className="text-2xl text-amber-500 mt-1" />
                <div>
                  <Text strong className="text-base text-amber-900 block">
                    Khu vực Đánh giá dành cho Học viên
                  </Text>
                  <Text type="secondary" className="text-xs text-amber-700">
                    Hãy gửi đánh giá cho Trainer để mở khóa xem điểm rèn luyện cá nhân và lời nhận xét mà Trainer dành cho bạn.
                  </Text>
                </div>
              </div>
              <Space>
                <Button
                  type="default"
                  icon={<TrophyOutlined className="text-yellow-600" />}
                  onClick={() => setIsMyResultOpen(true)}
                >
                  Điểm của tôi
                </Button>
                <Button
                  type="primary"
                  className="bg-amber-600 hover:!bg-amber-500"
                  icon={<StarOutlined />}
                  onClick={() => setIsTraineeEvalOpen(true)}
                >
                  Đánh giá Trainer
                </Button>
              </Space>
            </div>
          </Card>
        </div>
      )}

      {/* Metrics Row */}
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
                value={totalParticipants > 0 ? Math.round((checkedInCount / totalParticipants) * 100) : 0}
                suffix="%"
                valueStyle={{ color: '#4f46e5' }}
              />
            </Card>
          </Col>
        </Row>
      </div>

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
              children: (
                <Table
                  dataSource={meeting.participants}
                  columns={columns}
                  rowKey="user_id"
                  pagination={totalParticipants > 10 ? { pageSize: 10 } : false}
                  className="mt-2"
                />
              ),
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

      {/* Modals */}
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

      {evaluatingParticipant && (
        <TrainerEvaluationModal
          open={!!evaluatingParticipant}
          meetingId={meeting.id}
          trainee={evaluatingParticipant}
          onSuccess={() => {
            setEvaluatingParticipant(null);
            refetch();
          }}
          onClose={() => setEvaluatingParticipant(null)}
          onCancel={() => setEvaluatingParticipant(null)}
        />
      )}

      <TraineeEvaluationModal
        open={isTraineeEvalOpen}
        meetingId={meeting.id}
        trainerId={meeting.trainer?.id || meeting.created_by || undefined}
        trainerName={meeting.trainer?.name}
        trainerAvatarUrl={meeting.trainer?.avatar_url}
        onSuccess={() => {
          setIsTraineeEvalOpen(false);
          refetch();
        }}
        onClose={() => setIsTraineeEvalOpen(false)}
        onCancel={() => setIsTraineeEvalOpen(false)}
      />

      <MyEvaluationResultModal
        open={isMyResultOpen}
        meetingId={meeting.id}
        onClose={() => setIsMyResultOpen(false)}
      />

      <MeetingModal
        open={isEditMeetingModalOpen}
        editingItem={meeting}
        users={users}
        onSubmit={handleEditMeetingSubmit}
        onCancel={() => setIsEditMeetingModalOpen(false)}
      />
    </div>
  );
};

export default MeetingDetailPage;
