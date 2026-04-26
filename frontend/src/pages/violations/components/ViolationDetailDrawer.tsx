import { Drawer, Space, Descriptions, Avatar, Typography, Divider, Button, Popconfirm } from 'antd';
import { InfoCircleOutlined, UserOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ViolationResponse } from '@/types/activity.types';

const { Text } = Typography;

interface ViolationDetailDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    detailItem: ViolationResponse | null;
    canUpdate: boolean;
    canDelete: boolean;
    onEdit: (item: ViolationResponse) => void;
    onDelete: (id: number) => void;
    isMobile?: boolean;
}

const ViolationDetailDrawer = ({
    isOpen,
    onClose,
    detailItem,
    canUpdate,
    canDelete,
    onEdit,
    onDelete,
    isMobile
}: ViolationDetailDrawerProps) => {
    return (
        <Drawer
            title={
                <Space>
                    <InfoCircleOutlined className="text-red-500" />
                    <span>Chi tiết Vi phạm</span>
                </Space>
            }
            placement="right"
            onClose={onClose}
            open={isOpen}
            width={isMobile ? '100%' : 500}
        >
            {detailItem && (
                <div className="flex flex-col h-full">
                    <div className="flex-1">
                        <Descriptions column={1} bordered size="small" className="mb-6">
                            <Descriptions.Item label="Thành viên">
                                <Space>
                                    <Avatar
                                        src={detailItem.owner?.avatar || detailItem.user_avatar}
                                        icon={<UserOutlined />}
                                        size="small"
                                    />
                                    <Text strong>{detailItem.owner?.name || detailItem.user_name || 'Unknown'}</Text>
                                </Space>
                            </Descriptions.Item>
                            <Descriptions.Item label="Thời gian">
                                {dayjs(detailItem.date).format('DD/MM/YYYY HH:mm')}
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider style={{ textAlign: 'left' }} className="!mb-4">Lý do / Nội dung</Divider>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-100 text-gray-700 whitespace-pre-wrap">
                            {detailItem.reason}
                        </div>

                        <Divider style={{ textAlign: 'left' }} className="!mb-4">Thông tin hệ thống</Divider>
                        <Descriptions column={1} size="small" className="text-gray-500">
                            <Descriptions.Item label="Ngày ghi nhận">
                                {dayjs(detailItem.created_at).format('DD/MM/YYYY HH:mm:ss')}
                            </Descriptions.Item>
                            {detailItem.updated_at !== detailItem.created_at && (
                                <Descriptions.Item label="Cập nhật lần cuối">
                                    {dayjs(detailItem.updated_at).format('DD/MM/YYYY HH:mm:ss')}
                                </Descriptions.Item>
                            )}
                            {detailItem.creator && (
                                <Descriptions.Item label="Created by">
                                    <Space>
                                        <Avatar src={detailItem.creator.avatar} size="small" />
                                        <Text>{detailItem.creator.name}</Text>
                                    </Space>
                                </Descriptions.Item>
                            )}
                            {detailItem.updater && (
                                <Descriptions.Item label="Updated by">
                                    <Space>
                                        <Avatar src={detailItem.updater.avatar} size="small" />
                                        <Text>{detailItem.updater.name}</Text>
                                    </Space>
                                </Descriptions.Item>
                            )}
                        </Descriptions>
                    </div>

                    <div className="pt-4 border-t border-gray-100 flex justify-end gap-2">
                        {canUpdate && (
                            <Button
                                icon={<EditOutlined />}
                                onClick={() => onEdit(detailItem)}
                            >
                                Chỉnh sửa
                            </Button>
                        )}
                        {canDelete && (
                            <Popconfirm
                                title="Xóa vi phạm này?"
                                onConfirm={() => onDelete(detailItem.id)}
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Button danger icon={<DeleteOutlined />}>Xóa</Button>
                            </Popconfirm>
                        )}
                    </div>
                </div>
            )}
        </Drawer>
    );
};

export default ViolationDetailDrawer;
