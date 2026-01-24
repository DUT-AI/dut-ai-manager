import { Modal, Table, Avatar, Tag, Typography } from 'antd';
import { UserOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
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
            )
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: ParticipantStatus) => (
                <Tag color={status === ParticipantStatus.JOINED ? 'green' : 'default'} icon={status === ParticipantStatus.JOINED ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
                    {status.toUpperCase()}
                </Tag>
            )
        },
        {
            title: 'Thời gian check-in',
            dataIndex: 'check_in_at',
            key: 'check_in_at',
            render: (text: string) => text ? dayjs(text).format('HH:mm:ss DD/MM/YYYY') : '-'
        },
        {
            title: 'Ảnh check-in',
            dataIndex: 'link_image',
            key: 'link_image',
            render: (url: string) => url ? (
                <a href={url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline text-xs">Xem ảnh</a>
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
