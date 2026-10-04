import React from 'react';
import { Drawer, Descriptions, Tag, Space, Avatar, Typography, Button, Popconfirm, Card, Divider, Grid } from 'antd';
import {
    UserOutlined,
    EditOutlined,
    DeleteOutlined,
    FileTextOutlined,
    ClockCircleOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';
import { CATEGORY_COLORS, CATEGORY_LABELS } from './constants';

const { Title, Text } = Typography;

interface PermissionDetailDrawerProps {
    isOpen: boolean;
    item: PermissionRequestResponse | null;
    canUpdate: boolean;
    canDelete: boolean;
    onClose: () => void;
    onEdit: (item: PermissionRequestResponse) => void;
    onDelete: (id: number) => void;
}

export const PermissionDetailDrawer: React.FC<PermissionDetailDrawerProps> = ({
    isOpen,
    item,
    canUpdate,
    canDelete,
    onClose,
    onEdit,
    onDelete,
}) => {
    const screens = Grid.useBreakpoint();

    if (!item) return null;

    return (
        <Drawer
            title={
                <Space>
                    <InfoCircleOutlined className="text-indigo-500" />
                    <span>Chi tiết Đơn xin phép</span>
                </Space>
            }
            placement="right"
            onClose={onClose}
            open={isOpen}
            width={screens.md ? 500 : '100%'}
        >
            <div className="flex flex-col h-full">
                <div className="flex-1 overflow-y-auto px-1">
                    <Descriptions column={1} bordered size="small" className="mb-6 bg-white rounded-lg shadow-xs overflow-hidden">
                        <Descriptions.Item label="Người tạo">
                            <Space>
                                <Avatar size="small" src={item.owner?.avatar_url} icon={<UserOutlined />} />
                                <Text strong>{item.owner?.name || `#${item.created_by}`}</Text>
                            </Space>
                        </Descriptions.Item>
                        <Descriptions.Item label="Loại phép">
                            <Tag color={CATEGORY_COLORS[item.category.toLowerCase()] || 'default'} className="rounded-full px-3">
                                {CATEGORY_LABELS[item.category.toLowerCase()] || item.category}
                            </Tag>
                        </Descriptions.Item>
                        {item.start_time && (
                            <Descriptions.Item label="Thời gian">
                                {dayjs(item.start_time).format('DD/MM/YYYY HH:mm')}
                            </Descriptions.Item>
                        )}
                    </Descriptions>

                    {(item.homework || item.meeting) && (
                        <>
                            <Divider style={{ textAlign: 'left' }} className="mb-4!">Liên quan</Divider>
                            <div className="mb-6">
                                {item.homework && (
                                    <Card size="small" className="bg-indigo-50/30 border-indigo-100 rounded-lg">
                                        <Title level={5} className="mb-1! text-indigo-700">
                                            <Space><FileTextOutlined /> {item.homework.title}</Space>
                                        </Title>
                                        <Text type="secondary" className="text-xs">
                                            Deadline: {dayjs(item.homework.deadline).format('DD/MM/YYYY HH:mm')}
                                        </Text>
                                    </Card>
                                )}
                                {item.meeting && (
                                    <Card size="small" className="bg-purple-50/30 border-purple-100 rounded-lg">
                                        <Title level={5} className="mb-1! text-purple-700">
                                            <Space><ClockCircleOutlined /> {item.meeting.title}</Space>
                                        </Title>
                                        <Text type="secondary" className="text-xs">
                                            Ngày: {dayjs(item.meeting.start_time).format('DD/MM/YYYY')}
                                        </Text>
                                    </Card>
                                )}
                            </div>
                        </>
                    )}

                    <Divider style={{ textAlign: 'left' }} className="mb-4!">Nội dung / Lý do</Divider>
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 text-gray-700 whitespace-pre-wrap">
                        {item.note}
                    </div>

                    <Divider style={{ textAlign: 'left' }}>Thông tin hệ thống</Divider>
                    <Descriptions column={1} size="small" className="text-gray-500">
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(item.created_at).format('DD/MM/YYYY HH:mm:ss')}
                        </Descriptions.Item>
                        {item.updated_at !== item.created_at && (
                            <Descriptions.Item label="Cập nhật lần cuối">
                                {dayjs(item.updated_at).format('DD/MM/YYYY HH:mm:ss')}
                            </Descriptions.Item>
                        )}
                        {item.creator && (
                            <Descriptions.Item label="Created by">
                                {item.creator.name}
                            </Descriptions.Item>
                        )}
                        {item.updater && (
                            <Descriptions.Item label="Updated by">
                                {item.updater.name}
                            </Descriptions.Item>
                        )}
                    </Descriptions>
                </div>

                <div className="pt-4 border-t border-gray-100 flex justify-end gap-2">
                    {canUpdate && (
                        <Button
                            icon={<EditOutlined />}
                            onClick={() => onEdit(item)}
                        >
                            Chỉnh sửa
                        </Button>
                    )}
                    {canDelete && (
                        <Popconfirm
                            title="Xóa đơn này?"
                            onConfirm={() => onDelete(item.id)}
                            okText="Xóa"
                            cancelText="Hủy"
                        >
                            <Button danger icon={<DeleteOutlined />}>Xóa đơn</Button>
                        </Popconfirm>
                    )}
                </div>
            </div>
        </Drawer>
    );
};
