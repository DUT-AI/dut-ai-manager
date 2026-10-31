import { Modal, Table, Avatar, Tag, Typography, Image, Empty } from 'antd';
import {
    UserOutlined,
    CrownOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse, ParticipantResponse } from '@/features/meeting/types/meeting.types';
import { ParticipantRole, ParticipantStatus } from '@/features/meeting/types/meeting.types';
import { useMeetingDetail } from '@/features/meeting/hooks/useMeetings';

const { Text } = Typography;

interface Props {
    open: boolean;
    meeting: MeetingResponse | null;
    onCancel: () => void;
}

export const ParticipantListModal = ({ open, meeting, onCancel }: Props) => {
    const meetingId = meeting?.id ?? 0;
    const { data: detailMeeting, isLoading: isDetailLoading } = useMeetingDetail(open && meetingId > 0 ? meetingId : 0);

    const trainersList = detailMeeting?.trainers || [];
    const traineesList = detailMeeting?.trainees || [];

    const renderStatus = (status: ParticipantStatus) => {
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
    };

    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: ParticipantResponse) => (
                <div className="flex items-center gap-2">
                    <Avatar src={record.user_avatar_url} icon={<UserOutlined />} size="small" />
                    <div>
                        <Text strong className="text-sm block">{record.user_name || `User ID: ${record.user_id}`}</Text>
                        {record.role === ParticipantRole.TRAINER && (
                            <Tag color="gold" className="text-[10px] m-0">
                                <CrownOutlined className="mr-0.5" /> Trainer
                            </Tag>
                        )}
                    </div>
                </div>
            ),
            sorter: (a: ParticipantResponse, b: ParticipantResponse) => (a.user_name || '').localeCompare(b.user_name || ''),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: ParticipantStatus) => renderStatus(status),
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
            width={850}
            destroyOnClose
        >
            <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-1">
                {/* Bảng Giảng viên */}
                <div className="border border-amber-200/70 rounded-xl overflow-hidden bg-white shadow-xs">
                    <div className="bg-amber-50/70 px-4 py-2.5 border-b border-amber-100 flex items-center gap-2">
                        <CrownOutlined className="text-amber-600" />
                        <span className="font-semibold text-sm text-gray-800">
                            Giảng viên / Người phụ trách ({trainersList.length})
                        </span>
                    </div>
                    <Table
                        dataSource={trainersList}
                        loading={isDetailLoading}
                        columns={columns}
                        rowKey="user_id"
                        pagination={false}
                        size="small"
                        locale={{
                            emptyText: (
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description="Buổi tự học nhóm (không có Trainer phụ trách)"
                                />
                            ),
                        }}
                    />
                </div>

                {/* Bảng Học viên */}
                <div className="border border-blue-200/70 rounded-xl overflow-hidden bg-white shadow-xs">
                    <div className="bg-blue-50/70 px-4 py-2.5 border-b border-blue-100 flex items-center gap-2">
                        <UserOutlined className="text-blue-600" />
                        <span className="font-semibold text-sm text-gray-800">
                            Học viên / Thành viên tham gia ({traineesList.length})
                        </span>
                    </div>
                    <Table
                        dataSource={traineesList}
                        loading={isDetailLoading}
                        columns={columns}
                        rowKey="user_id"
                        pagination={traineesList.length > 10 ? { pageSize: 10 } : false}
                        size="small"
                        locale={{
                            emptyText: (
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description="Chưa có học viên nào tham gia"
                                />
                            ),
                        }}
                    />
                </div>
            </div>
        </Modal>
    );
};
