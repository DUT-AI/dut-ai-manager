import { Modal, Table, Avatar, Tag, Typography, Image } from 'antd';
import { UserOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse, ParticipantResponse } from '@/features/meeting/types/meeting.types';
import { ParticipantStatus } from '@/features/meeting/types/meeting.types';

const { Text } = Typography;

interface Props {
    open: boolean;
    meeting: MeetingResponse | null;
    onCancel: () => void;
}

export const ParticipantListModal = ({ open, meeting, onCancel }: Props) => {
    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: ParticipantResponse) => (
                <div className="flex items-center gap-2">
                    <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="small" />
                    <Text>{record.user_name || `User ID: ${record.user_id}`}</Text>
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
                let tagText = 'CHƯA CHECKIN';

                switch (status) {
                    case ParticipantStatus.JOINED:
                        tagColor = 'green';
                        tagIcon = <CheckCircleOutlined />;
                        tagText = 'ĐÃ CHECKIN';
                        break;
                    case ParticipantStatus.LATE_EXCUSED:
                        tagColor = 'blue';
                        tagIcon = <ClockCircleOutlined />;
                        tagText = 'TRỄ (CÓ PHÉP)';
                        break;
                    case ParticipantStatus.LATE_UNEXCUSED:
                        tagColor = 'orange';
                        tagIcon = <ClockCircleOutlined />;
                        tagText = 'TRỄ (KHÔNG PHÉP)';
                        break;
                    case ParticipantStatus.ABSENT_EXCUSED:
                        tagColor = 'purple';
                        tagIcon = <CloseCircleOutlined />;
                        tagText = 'VẮNG (CÓ PHÉP)';
                        break;
                    case ParticipantStatus.ABSENT_UNEXCUSED:
                        tagColor = 'red';
                        tagIcon = <CloseCircleOutlined />;
                        tagText = 'VẮNG (KHÔNG PHÉP)';
                        break;
                    case ParticipantStatus.COMPLETED:
                        tagColor = 'cyan';
                        tagIcon = <CheckCircleOutlined />;
                        tagText = 'HOÀN THÀNH';
                        break;
                    case ParticipantStatus.NOT_JOINED:
                    default:
                        tagColor = 'default';
                        tagIcon = <CloseCircleOutlined />;
                        tagText = 'CHƯA CHECKIN';
                        break;
                }

                return (
                    <Tag color={tagColor} icon={tagIcon}>
                        {tagText}
                    </Tag>
                );
            },
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => a.status.localeCompare(b.status),
        },
        {
            title: 'Thời gian check-in',
            dataIndex: 'check_in_at',
            key: 'check_in_at',
            render: (text: string) => text ? dayjs(text).format('HH:mm:ss DD/MM/YYYY') : '-',
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
                if (!a.check_in_at) return 1;
                if (!b.check_in_at) return -1;
                return dayjs(a.check_in_at).unix() - dayjs(b.check_in_at).unix();
            },
        },
        {
            title: 'Thời gian check-out',
            dataIndex: 'check_out_at',
            key: 'check_out_at',
            render: (text: string) => text ? dayjs(text).format('HH:mm:ss DD/MM/YYYY') : '-',
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => {
                if (!a.check_out_at) return 1;
                if (!b.check_out_at) return -1;
                return dayjs(a.check_out_at).unix() - dayjs(b.check_out_at).unix();
            },
        },
        {
            title: 'Ảnh check-in',
            dataIndex: 'link_image',
            key: 'link_image',
            render: (url: string) => url ? (
                <Image
                    src={url}
                    alt="Checkin"
                    width={40}
                    className="rounded cursor-pointer hover:opacity-80 transition-opacity"
                    preview={{
                        mask: <div className="text-[10px]">Xem</div>
                    }}
                />
            ) : '-'
        }
    ];

    return (
        <Modal
            title={
                <div className="flex flex-col">
                    <Text strong>Danh sách tham gia: {meeting?.title}</Text>
                    <Text type="secondary" className="text-xs font-normal">
                        Thời gian: {meeting ? `${dayjs(meeting.start_time).format('HH:mm')} - ${dayjs(meeting.end_time).format('HH:mm')} (${dayjs(meeting.start_time).format('DD/MM/YYYY')})` : ''}
                    </Text>
                </div>
            }
            open={open}
            onCancel={onCancel}
            footer={null}
            width={800}
            destroyOnClose
        >
            <Table
                dataSource={meeting?.participants || []}
                columns={columns}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                size="middle"
            />
        </Modal>
    );
};
