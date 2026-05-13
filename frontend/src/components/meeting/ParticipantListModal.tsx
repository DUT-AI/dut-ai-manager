import { Modal, Table, Avatar, Tag, Typography, Image } from 'antd';
import { UserOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse, ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';

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
                    <Avatar src={record.user_avatar} icon={<UserOutlined />} size="small" />
                    <Text>{record.user_name || `User ID: ${record.user_id}`}</Text>
                </div>
            ),
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => (a.user_name || '').localeCompare(b.user_name || ''),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: ParticipantStatus, record: ParticipantResponse) => {
                const isLateNotJoined = status === ParticipantStatus.NOT_JOINED && meeting && dayjs().isAfter(dayjs(meeting.start_time).add(5, 'minute'));
                const isLateJoined = status === ParticipantStatus.JOINED && record.check_in_at && meeting && dayjs(record.check_in_at).isAfter(dayjs(meeting.start_time).add(5, 'minute'));
                
                return (
                    <Tag 
                        color={status === ParticipantStatus.JOINED ? (isLateJoined ? 'warning' : 'green') : isLateNotJoined ? 'orange' : 'default'} 
                        icon={status === ParticipantStatus.JOINED ? <CheckCircleOutlined /> : isLateNotJoined ? <ClockCircleOutlined /> : <CloseCircleOutlined />}
                    >
                        {status === ParticipantStatus.JOINED ? (isLateJoined ? 'TRỄ (ĐÃ CÓ MẶT)' : 'ĐÃ CHECKIN') : isLateNotJoined ? 'TRỄ (CHƯA CÓ MẶT)' : 'CHƯA THAM GIA'}
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
