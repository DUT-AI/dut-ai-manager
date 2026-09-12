import { useState } from 'react';
import { Drawer, Table, Avatar, Tag, Typography, Descriptions, Button, Popconfirm, Image, Tooltip } from 'antd';
import {
    UserOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    EditOutlined,
    DeleteOutlined,
    SafetyCertificateOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse, ParticipantResponse, UpdateParticipantStatusPayload } from '@/features/meeting/types/meeting.types';
import { ParticipantStatus } from '@/features/meeting/types/meeting.types';
import { useMeetingEvents } from '@/features/meeting/hooks/useMeetingEvents';
import { useUpdateParticipantStatus } from '@/features/meeting/hooks/useMeetings';
import { EditParticipantStatusModal } from './EditParticipantStatusModal';

const { Text, Title } = Typography;

interface Props {
    open: boolean;
    meeting: MeetingResponse | null;
    onClose: () => void;
    onEdit?: (meeting: MeetingResponse) => void;
    onDelete?: (id: number) => void;
}

export const MeetingDetailDrawer = ({ open, meeting, onClose, onEdit, onDelete }: Props) => {
    const [editingParticipant, setEditingParticipant] = useState<ParticipantResponse | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    // Mutation hook để cập nhật trạng thái participant
    const updateParticipantStatusMutation = useUpdateParticipantStatus();

    // Lắng nghe sự kiện SSE cho buổi họp này chỉ khi drawer đang mở
    useMeetingEvents(meeting?.id, open);

    if (!meeting) return null;

    const checkedIn = meeting.participants.filter(
        p => p.status === ParticipantStatus.JOINED ||
             p.status === ParticipantStatus.LATE_EXCUSED ||
             p.status === ParticipantStatus.LATE_UNEXCUSED ||
             p.status === ParticipantStatus.COMPLETED
    ).length;
    const total = meeting.participants.length;
    const isOngoing = dayjs().isAfter(dayjs(meeting.start_time)) && dayjs().isBefore(dayjs(meeting.end_time));
    const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

    const handleUpdateStatus = async (payload: UpdateParticipantStatusPayload) => {
        if (!editingParticipant || !meeting) return;
        await updateParticipantStatusMutation.mutateAsync({
            meetingId: meeting.id,
            userId: editingParticipant.user_id,
            payload,
        });
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
                    <Tag color={tagColor} icon={tagIcon}>
                        {tagText}
                    </Tag>
                );
            },
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
                // Nếu không checkout mà meeting đã kết thúc và thành viên có checkin
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
            render: (_: unknown, record: ParticipantResponse) => (
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
            ),
        },
    ];

    return (
        <Drawer
            title={null}
            open={open}
            onClose={onClose}
            width={720}
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

                {/* Participants table */}
                <Text strong className="block mb-2">
                    Danh sách tham gia ({total})
                </Text>
                <Table
                    dataSource={meeting.participants}
                    columns={columns}
                    rowKey="user_id"
                    pagination={total > 10 ? { pageSize: 10, size: 'small' } : false}
                    size="small"
                    className="meeting-detail-table"
                />
            </div>

            {/* Edit Participant Status Modal */}
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
