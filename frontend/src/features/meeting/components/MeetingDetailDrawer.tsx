import { useState } from 'react';
import { Drawer, Table, Avatar, Tag, Typography, Descriptions, Button, Popconfirm, Image, Tooltip, Tabs, Space, message } from 'antd';
import {
    UserOutlined,
    CheckCircleOutlined,
    CheckOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    EditOutlined,
    DeleteOutlined,
    SafetyCertificateOutlined,
    StarOutlined,
    TrophyOutlined,
    BarChartOutlined,
    TeamOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse, MeetingDetailResponse, ParticipantResponse, UpdateParticipantStatusPayload } from '@/features/meeting/types/meeting.types';
import { ParticipantStatus } from '@/features/meeting/types/meeting.types';
import { useMeetingEvents } from '@/features/meeting/hooks/useMeetingEvents';
import { useMeetingDetail, useUpdateParticipantStatus } from '@/features/meeting/hooks/useMeetings';
import { useAuth } from '@/features/auth/context/AuthContext';
import { ParticipantStatusTag } from './ParticipantStatusTag';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';
import { TrainerEvaluationModal } from './TrainerEvaluationModal';
import { TraineeEvaluationModal } from './TraineeEvaluationModal';
import { MeetingEvaluationSummaryView } from './MeetingEvaluationSummaryView';
import { MyEvaluationResultModal } from './MyEvaluationResultModal';

const { Text, Title } = Typography;

interface Props {
    open: boolean;
    meeting: MeetingResponse | MeetingDetailResponse | null;
    onClose: () => void;
    onEdit?: (meeting: MeetingResponse) => void;
    onDelete?: (id: number) => void;
}

export const MeetingDetailDrawer = ({ open, meeting: initialMeeting, onClose, onEdit, onDelete }: Props) => {
    const { user } = useAuth();
    const meetingId = initialMeeting?.id ?? 0;
    const { data: fetchedDetail, refetch } = useMeetingDetail(open && meetingId > 0 ? meetingId : 0);
    const meeting = fetchedDetail || initialMeeting;

    const [activeTab, setActiveTab] = useState('participants');
    const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    // Evaluation modal states
    const [evaluatingParticipant, setEvaluatingParticipant] = useState<ParticipantResponse | null>(null);
    const [isTraineeEvalOpen, setIsTraineeEvalOpen] = useState(false);
    const [isMyResultOpen, setIsMyResultOpen] = useState(false);

    const [quickCheckInLoadingId, setQuickCheckInLoadingId] = useState<number | null>(null);
    const [isCheckingInAll, setIsCheckingInAll] = useState(false);

    // Mutation hook để cập nhật trạng thái participant
    const updateParticipantStatusMutation = useUpdateParticipantStatus();

    // Lắng nghe sự kiện SSE cho buổi họp này chỉ khi drawer đang mở
    useMeetingEvents(meeting?.id, open);

    if (!meeting) return null;

    const participantsList = ('participants' in meeting && meeting.participants) ? meeting.participants : [];
    const isTrainer =
        (meeting.created_by ? currentUserId === meeting.created_by : false) ||
        (meeting.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
        (user?.role_names?.some(r => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);
    const myParticipantRecord = participantsList.find(p => p.user_id === currentUserId);
    const isTrainee = !!myParticipantRecord;

    const checkedIn = participantsList.filter(
        p => p.status === ParticipantStatus.JOINED ||
             p.status === ParticipantStatus.LATE_EXCUSED ||
             p.status === ParticipantStatus.LATE_UNEXCUSED ||
             p.status === ParticipantStatus.COMPLETED
    ).length;
    const total = participantsList.length;
    const unjoinedParticipants = participantsList.filter(
        p => p.status === ParticipantStatus.NOT_JOINED && !p.check_in_at
    );
    const unjoinedCount = unjoinedParticipants.length;

    const isOngoing = dayjs().isAfter(dayjs(meeting.start_time)) && dayjs().isBefore(dayjs(meeting.end_time));
    const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

    const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
        if (!editingParticipant || !meeting) return;
        await updateParticipantStatusMutation.mutateAsync({
            meetingId: meeting.id,
            userId: editingParticipant.user_id,
            payload,
        });
        refetch();
    };

    const handleQuickCheckIn = async (record: ParticipantResponse, isCheckIn: boolean) => {
        if (!meeting) return;
        try {
            setQuickCheckInLoadingId(record.user_id);
            if (isCheckIn) {
                await updateParticipantStatusMutation.mutateAsync({
                    meetingId: meeting.id,
                    userId: record.user_id,
                    payload: {
                        status: ParticipantStatus.JOINED,
                        check_in_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
                    },
                });
                message.success(`Đã điểm danh cho ${record.user_name || 'học viên'}`);
            } else {
                await updateParticipantStatusMutation.mutateAsync({
                    meetingId: meeting.id,
                    userId: record.user_id,
                    payload: {
                        status: ParticipantStatus.NOT_JOINED,
                        check_in_at: null,
                        check_out_at: null,
                    },
                });
                message.success(`Đã hủy điểm danh cho ${record.user_name || 'học viên'}`);
            }
            refetch();
        } catch {
            message.error(isCheckIn ? 'Điểm danh thất bại' : 'Hủy điểm danh thất bại');
        } finally {
            setQuickCheckInLoadingId(null);
        }
    };

    const handleQuickCheckInAll = async () => {
        if (!meeting || unjoinedCount === 0) return;
        try {
            setIsCheckingInAll(true);
            const promises = unjoinedParticipants.map((p) =>
                updateParticipantStatusMutation.mutateAsync({
                    meetingId: meeting.id,
                    userId: p.user_id,
                    payload: {
                        status: ParticipantStatus.JOINED,
                        check_in_at: dayjs().format('YYYY-MM-DDTHH:mm:ss'),
                    },
                })
            );
            await Promise.all(promises);
            message.success(`Đã điểm danh thành công cho ${unjoinedCount} học viên`);
            refetch();
        } catch {
            message.error('Có lỗi xảy ra khi điểm danh tất cả');
        } finally {
            setIsCheckingInAll(false);
        }
    };

    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: unknown, record: ParticipantResponse) => (
                <div className="flex items-center gap-2">
                    <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="small" />
                    <Text>{record.user_name || `User #${record.user_id}`}</Text>
                </div>
            ),
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => (a.user_name || '').localeCompare(b.user_name || ''),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: any) => <ParticipantStatusTag status={status} />,
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => (a.status || '').localeCompare(b.status || ''),
        },
        {
            title: 'Checkin',
            dataIndex: 'check_in_at',
            key: 'check_in_at',
            render: (text: string) => text ? dayjs(text).format('HH:mm:ss') : '—',
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
                if (!a.check_in_at) return 1;
                if (!b.check_in_at) return -1;
                return dayjs(a.check_in_at).unix() - dayjs(b.check_in_at).unix();
            },
        },
        {
            title: 'Checkout',
            dataIndex: 'check_out_at',
            key: 'check_out_at',
            render: (text: string, record: ParticipantResponse) => {
                if (text) return dayjs(text).format('HH:mm:ss');
                if (isEnded && record.check_in_at) {
                    return dayjs(meeting.end_time).format('HH:mm:ss');
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
            title: 'Ảnh',
            dataIndex: 'link_image',
            key: 'link_image',
            render: (url: string) =>
                url ? (
                    <Image
                        src={url}
                        alt="Checkin"
                        width={40}
                        className="rounded cursor-pointer hover:opacity-80 transition-opacity"
                        preview={{
                            mask: <div className="text-[10px]">Xem</div>
                        }}
                    />
                ) : (
                    '—'
                ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            render: (_: unknown, record: ParticipantResponse) => {
                const isJoined =
                    record.status === ParticipantStatus.JOINED ||
                    record.status === ParticipantStatus.LATE_EXCUSED ||
                    record.status === ParticipantStatus.LATE_UNEXCUSED ||
                    record.status === ParticipantStatus.COMPLETED;

                return (
                    <Space size={4}>
                        {isTrainer && (
                            <>
                                {!isJoined ? (
                                    <Button
                                        type="primary"
                                        size="small"
                                        icon={<ThunderboltOutlined />}
                                        className="bg-emerald-600 hover:!bg-emerald-500 text-white text-xs px-2"
                                        loading={quickCheckInLoadingId === record.user_id}
                                        onClick={() => handleQuickCheckIn(record, true)}
                                    >
                                        Check-in
                                    </Button>
                                ) : (
                                    <Popconfirm
                                        title="Hủy điểm danh?"
                                        description={`Bạn có chắc muốn hủy điểm danh của ${record.user_name || 'học viên này'}?`}
                                        onConfirm={() => handleQuickCheckIn(record, false)}
                                        okText="Hủy check-in"
                                        cancelText="Đóng"
                                    >
                                        <Button
                                            size="small"
                                            icon={<CheckOutlined />}
                                            className="text-emerald-700 bg-emerald-50 border-emerald-300 hover:!bg-emerald-100 text-xs px-2"
                                            loading={quickCheckInLoadingId === record.user_id}
                                        >
                                            Đã Check-in
                                        </Button>
                                    </Popconfirm>
                                )}
                            </>
                        )}

                        {meeting.enable_evaluation && isTrainer && (
                            <Tooltip
                                title={
                                    record.status === ParticipantStatus.ABSENT_EXCUSED ||
                                    record.status === ParticipantStatus.ABSENT_UNEXCUSED
                                        ? 'Học viên vắng mặt không thể đánh giá'
                                        : 'Đánh giá học viên này'
                                }
                            >
                                <Button
                                    icon={<StarOutlined className="text-amber-500" />}
                                    size="small"
                                    type="text"
                                    disabled={
                                        record.status === ParticipantStatus.ABSENT_EXCUSED ||
                                        record.status === ParticipantStatus.ABSENT_UNEXCUSED
                                    }
                                    onClick={() => setEvaluatingParticipant(record)}
                                />
                            </Tooltip>
                        )}
                        {isTrainer && (
                            <Tooltip title="Chỉnh sửa trạng thái">
                                <Button
                                    icon={<EditOutlined />}
                                    size="small"
                                    type="text"
                                    onClick={() => {
                                        setEditingParticipant(record);
                                        setIsEditModalOpen(true);
                                    }}
                                />
                            </Tooltip>
                        )}
                    </Space>
                );
            },
        },
    ];

    return (
        <Drawer
            title={null}
            open={open}
            onClose={onClose}
            width={760}
            styles={{ body: { padding: 0 } }}
        >
            {/* Header */}
            <div
                className="px-6 py-5"
                style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
            >
                <div className="flex items-start justify-between">
                    <div>
                        <Title level={4} className="!text-white !mb-1">
                            {meeting.title}
                        </Title>
                        <div className="flex items-center gap-3 text-white/80 text-sm">
                            <span className="flex items-center gap-1">
                                <ClockCircleOutlined />
                                {dayjs(meeting.start_time).format('HH:mm')} – {dayjs(meeting.end_time).format('HH:mm')}
                            </span>
                            <span>{dayjs(meeting.start_time).format('DD/MM/YYYY')}</span>
                        </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                        <Tag
                            color={isOngoing ? 'processing' : isEnded ? 'default' : 'blue'}
                            className="!m-0"
                        >
                            {isOngoing ? '🟢 Đang diễn ra' : isEnded ? '⚫ Đã kết thúc' : '🔵 Chưa bắt đầu'}
                        </Tag>
                        {meeting.require_check_in && (
                            <Tag icon={<SafetyCertificateOutlined />} color="orange" className="!m-0 !mt-1">
                                Kiểm tra checkin
                            </Tag>
                        )}
                        {meeting.enable_evaluation && (
                            <Tag icon={<StarOutlined />} color="gold" className="!m-0 !mt-1">
                                Đánh giá 2 chiều (24h)
                            </Tag>
                        )}
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="px-6 py-4">
                {/* Info */}
                <Descriptions
                    size="small"
                    column={2}
                    className="mb-4"
                    items={[
                        {
                            key: 'checkin',
                            label: 'Đã điểm danh',
                            children: (
                                <Text strong className="text-green-600">
                                    {checkedIn}/{total}
                                </Text>
                            ),
                        },
                        {
                            key: 'duration',
                            label: 'Thời lượng',
                            children: `${dayjs(meeting.end_time).diff(dayjs(meeting.start_time), 'minute')} phút`,
                        },
                        ...(meeting.content
                            ? [
                                {
                                    key: 'content',
                                    label: 'Nội dung',
                                    span: 2 as const,
                                    children: meeting.content,
                                },
                            ]
                            : []),
                    ]}
                />

                {/* Trainee Action Banner if evaluation enabled */}
                {meeting.enable_evaluation && (isTrainee || isTrainer) && (
                    <div className="mb-4 p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200 flex items-center justify-between">
                        <div>
                            <Text strong className="text-amber-900 block text-sm">
                                🌟 Đánh giá buổi học & Giảng viên
                            </Text>
                            <Text type="secondary" className="text-xs">
                                Hãy đánh giá Trainer để mở khóa xem điểm rèn luyện cá nhân của bạn.
                            </Text>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                size="small"
                                icon={<TrophyOutlined />}
                                onClick={() => setIsMyResultOpen(true)}
                            >
                                Điểm của tôi
                            </Button>
                            <Button
                                type="primary"
                                size="small"
                                className="bg-amber-600 hover:!bg-amber-500"
                                icon={<StarOutlined />}
                                onClick={() => setIsTraineeEvalOpen(true)}
                            >
                                Đánh giá Trainer
                            </Button>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mb-4">
                    {onEdit && (
                        <Button
                            icon={<EditOutlined />}
                            onClick={() => onEdit(meeting)}
                            size="small"
                        >
                            Chỉnh sửa meeting
                        </Button>
                    )}
                    {onDelete && (
                        <Popconfirm
                            title="Xóa buổi sinh hoạt?"
                            description="Bạn có chắc muốn xóa buổi sinh hoạt này?"
                            onConfirm={() => onDelete(meeting.id)}
                            okText="Xóa"
                            cancelText="Hủy"
                        >
                            <Button icon={<DeleteOutlined />} danger size="small">
                                Xóa meeting
                            </Button>
                        </Popconfirm>
                    )}
                </div>

                {/* Tabs: Danh sách & Báo cáo Đánh giá */}
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={[
                        {
                            key: 'participants',
                            label: (
                                <span>
                                    <TeamOutlined />
                                    Danh sách tham gia ({total})
                                </span>
                            ),
                            children: (
                                <div className="space-y-3">
                                    {isTrainer && unjoinedCount > 0 && (
                                        <div className="flex items-center justify-between gap-2 bg-emerald-50 border border-emerald-200 rounded-lg p-2.5">
                                            <div className="flex items-center gap-2">
                                                <ThunderboltOutlined className="text-emerald-600" />
                                                <span className="text-xs text-emerald-950">
                                                    Còn <strong>{unjoinedCount}</strong> học viên chưa check-in.
                                                </span>
                                            </div>
                                            <Popconfirm
                                                title="Điểm danh tất cả?"
                                                description={`Điểm danh nhanh cho ${unjoinedCount} học viên?`}
                                                onConfirm={handleQuickCheckInAll}
                                                okText="Điểm danh"
                                                cancelText="Hủy"
                                                disabled={isCheckingInAll}
                                            >
                                                <Button
                                                    type="primary"
                                                    size="small"
                                                    icon={<ThunderboltOutlined />}
                                                    className="bg-emerald-600 hover:!bg-emerald-500 text-xs"
                                                    loading={isCheckingInAll}
                                                >
                                                    Điểm danh tất cả ({unjoinedCount})
                                                </Button>
                                            </Popconfirm>
                                        </div>
                                    )}
                                    <Table
                                        dataSource={participantsList}
                                        columns={columns}
                                        rowKey="user_id"
                                        pagination={total > 10 ? { pageSize: 10, size: 'small' } : false}
                                        size="small"
                                        className="meeting-detail-table"
                                    />
                                </div>
                            ),
                        },
                        ...(meeting.enable_evaluation
                            ? [
                                {
                                    key: 'evaluations',
                                    label: (
                                        <span>
                                            <BarChartOutlined />
                                            Báo cáo Đánh giá
                                        </span>
                                    ),
                                    children: (
                                        <MeetingEvaluationSummaryView meetingId={meeting.id} />
                                    ),
                                },
                            ]
                            : []),
                    ]}
                />
            </div>

            {/* Modals */}
            <EditParticipantStatusModal
                open={isEditModalOpen}
                participant={editingParticipant}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setEditingParticipant(null);
                }}
                onSubmit={handleUpdateStatus}
                loading={updateParticipantStatusMutation.isPending}
            />

            {evaluatingParticipant && (
                <TrainerEvaluationModal
                    open={!!evaluatingParticipant}
                    meetingId={meeting.id}
                    trainee={{
                        user_id: evaluatingParticipant.user_id,
                        user_name: evaluatingParticipant.user_name,
                        user_avatar_url: evaluatingParticipant.user_avatar_url,
                    }}
                    onClose={() => setEvaluatingParticipant(null)}
                    onSuccess={() => setEvaluatingParticipant(null)}
                />
            )}

            <TraineeEvaluationModal
                open={isTraineeEvalOpen}
                meetingId={meeting.id}
                trainerId={meeting.trainer?.id || meeting.created_by || undefined}
                trainerName={meeting.trainer?.name || 'Trainer'}
                trainerAvatarUrl={meeting.trainer?.avatar_url || undefined}
                onClose={() => setIsTraineeEvalOpen(false)}
                onSuccess={() => setIsTraineeEvalOpen(false)}
            />

            <MyEvaluationResultModal
                open={isMyResultOpen}
                meetingId={meeting.id}
                onClose={() => setIsMyResultOpen(false)}
            />

            <style>{`
                .meeting-detail-table .ant-table-thead > tr > th {
                    background: #f8fafc !important;
                    font-size: 12px;
                    font-weight: 600;
                }
                .meeting-detail-table .ant-table-tbody > tr > td {
                    font-size: 13px;
                }
            `}</style>
        </Drawer>
    );
};
