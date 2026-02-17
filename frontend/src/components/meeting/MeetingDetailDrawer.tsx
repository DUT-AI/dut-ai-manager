import { Drawer, Table, Avatar, Tag, Typography, Descriptions, Button, Popconfirm } from 'antd';
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
import type { MeetingResponse, ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';

const { Text, Title } = Typography;

interface Props {
    open: boolean;
    meeting: MeetingResponse | null;
    onClose: () => void;
    onEdit?: (meeting: MeetingResponse) => void;
    onDelete?: (id: number) => void;
}

export const MeetingDetailDrawer = ({ open, meeting, onClose, onEdit, onDelete }: Props) => {
    if (!meeting) return null;

    const checkedIn = meeting.participants.filter(p => p.status === ParticipantStatus.JOINED).length;
    const total = meeting.participants.length;
    const isOngoing = dayjs().isAfter(dayjs(meeting.start_time)) && dayjs().isBefore(dayjs(meeting.end_time));
    const isEnded = dayjs().isAfter(dayjs(meeting.end_time));

    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: unknown, record: ParticipantResponse) => (
                <div className="flex items-center gap-2">
                    <Avatar src={record.user_avatar} icon={<UserOutlined />} size="small" />
                    <Text>{record.user_name || `User #${record.user_id}`}</Text>
                </div>
            ),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: ParticipantStatus) => (
                <Tag
                    color={status === ParticipantStatus.JOINED ? 'green' : 'default'}
                    icon={status === ParticipantStatus.JOINED ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                >
                    {status === ParticipantStatus.JOINED ? 'Đã checkin' : 'Chưa tham gia'}
                </Tag>
            ),
        },
        {
            title: 'Thời gian checkin',
            dataIndex: 'check_in_at',
            key: 'check_in_at',
            render: (text: string) => text ? dayjs(text).format('HH:mm:ss') : '—',
        },
        {
            title: 'Ảnh',
            dataIndex: 'link_image',
            key: 'link_image',
            render: (url: string) =>
                url ? (
                    <a href={url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline text-xs">
                        Xem ảnh
                    </a>
                ) : (
                    '—'
                ),
        },
    ];

    return (
        <Drawer
            title={null}
            open={open}
            onClose={onClose}
            width={680}
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
                            label: 'Đã checkin',
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
                            Chỉnh sửa
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
                                Xóa
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
