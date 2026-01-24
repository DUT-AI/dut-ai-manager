import { Typography, List, Card, Badge, Button, Empty } from 'antd';
import { VideoCameraOutlined, UserOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MeetingResponse } from '@/types/meeting.types';

const { Text } = Typography;

interface Props {
    data: MeetingResponse[];
    onViewParticipants: (meeting: MeetingResponse) => void;
    onEdit: (meeting: MeetingResponse) => void;
    onDelete: (id: number) => void;
}

export const MeetingSection = ({ data, onViewParticipants, onEdit, onDelete }: Props) => {
    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-2">
                <VideoCameraOutlined className="text-xl text-blue-500" />
                <Text strong className="text-lg">Buổi sinh hoạt ({data.length})</Text>
            </div>

            {data.length === 0 ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Không có buổi sinh hoạt" />
            ) : (
                <List
                    dataSource={data}
                    renderItem={(item) => (
                        <Card size="small" className="mb-3 hover:border-blue-300 transition-colors shadow-xs">
                            <div className="flex flex-col gap-2">
                                <div className="flex justify-between items-start">
                                    <Text strong className="text-blue-600 block">{item.title}</Text>
                                    <Badge
                                        status="processing"
                                        text={`${item.participants.filter(p => p.status === 'đã checkin').length}/${item.participants.length}`}
                                    />
                                </div>

                                {item.content && (
                                    <Text type="secondary" className="text-xs italic">{item.content}</Text>
                                )}

                                <div className="flex items-center gap-4 mt-1 text-gray-500 text-xs">
                                    <div className="flex items-center gap-1">
                                        <ClockCircleOutlined />
                                        <span>{dayjs(item.start_time).format('HH:mm')} - {dayjs(item.end_time).format('HH:mm')}</span>
                                    </div>
                                    <Button
                                        type="link"
                                        size="small"
                                        icon={<UserOutlined />}
                                        onClick={() => onViewParticipants(item)}
                                        className="p-0 h-auto"
                                    >
                                        DS tham gia
                                    </Button>
                                    <Button
                                        type="link"
                                        size="small"
                                        onClick={() => onEdit(item)}
                                        className="p-0 h-auto text-blue-500"
                                    >
                                        Sửa
                                    </Button>
                                    <Button
                                        type="link"
                                        size="small"
                                        danger
                                        onClick={() => onDelete(item.id)}
                                        className="p-0 h-auto"
                                    >
                                        Xóa
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    )}
                />
            )}
        </div>
    );
};
