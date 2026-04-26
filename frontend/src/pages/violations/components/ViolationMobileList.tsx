import { Card, Space, List, Avatar, Typography, Button, Popconfirm } from 'antd';
import { CalendarOutlined, UserOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ViolationResponse } from '@/types/activity.types';

const { Text } = Typography;

interface ViolationMobileListProps {
    violations: ViolationResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onViewDetail: (item: ViolationResponse) => void;
    onEdit: (item: ViolationResponse) => void;
    onDelete: (id: number) => void;
}

const ViolationMobileList = ({ 
    violations, 
    isLoading, 
    canUpdate, 
    canDelete, 
    onViewDetail, 
    onEdit, 
    onDelete 
}: ViolationMobileListProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={violations}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 !mb-4 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                        onClick={() => onViewDetail(record)}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Space className="text-gray-400 text-xs">
                                <CalendarOutlined />
                                <span>{dayjs(record.date).format('DD/MM/YYYY HH:mm')}</span>
                            </Space>
                        </div>

                        <div className="flex items-center gap-3 mb-4">
                            <Avatar
                                src={record.owner?.avatar || record.user_avatar}
                                icon={<UserOutlined />}
                                className="bg-linear-to-br from-red-500 to-orange-500 shadow-sm shrink-0"
                                size="large"
                            />
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="truncate text-base">
                                    {record.owner?.name || record.user_name || 'Unknown'}
                                </Text>
                                <Text type="danger" className="text-xs italic truncate">
                                    {record.reason}
                                </Text>
                            </div>
                        </div>

                        <div 
                            role="presentation" 
                            className="flex justify-end items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3 gap-2" 
                            onClick={(e) => e.stopPropagation()} 
                            onKeyDown={(e) => e.stopPropagation()}
                        >
                            <Button
                                icon={<EditOutlined />}
                                size="small"
                                onClick={() => onEdit(record)}
                                disabled={!canUpdate}
                            >
                                Sửa
                            </Button>
                            <Popconfirm
                                title="Xóa vi phạm này?"
                                onConfirm={() => onDelete(record.id)}
                                disabled={!canDelete}
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete}>Xóa</Button>
                            </Popconfirm>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

export default ViolationMobileList;
