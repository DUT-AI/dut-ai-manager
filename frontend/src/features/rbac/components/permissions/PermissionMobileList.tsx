import React from 'react';
import { List, Card, Tag, Space, Avatar, Typography, Button, Popconfirm } from 'antd';
import {
    UserOutlined,
    EditOutlined,
    DeleteOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';
import { CATEGORY_COLORS, CATEGORY_LABELS } from './constants';

const { Text } = Typography;

interface PermissionMobileListProps {
    permissions: PermissionRequestResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onViewDetail: (item: PermissionRequestResponse) => void;
    onEdit: (item: PermissionRequestResponse) => void;
    onDelete: (id: number) => void;
}

export const PermissionMobileList: React.FC<PermissionMobileListProps> = ({
    permissions,
    isLoading,
    canUpdate,
    canDelete,
    onViewDetail,
    onEdit,
    onDelete,
}) => {
    return (
        <div className="mt-4 px-3">
            <List
                dataSource={permissions}
                loading={isLoading}
                split={false}
                renderItem={(record) => (
                    <List.Item className="px-2 mb-4! border-0!">
                        <Card
                            className="w-full shadow-sm border-gray-100 overflow-hidden"
                            styles={{ body: { padding: '16px' } }}
                            onClick={() => onViewDetail(record)}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <Tag color={CATEGORY_COLORS[record.category.toLowerCase()] || 'default'} className="m-0 font-medium px-3 rounded-full">
                                    {CATEGORY_LABELS[record.category.toLowerCase()] || record.category}
                                </Tag>
                                <Space className="text-gray-400 text-xs">
                                    <InfoCircleOutlined />
                                    <span className="max-w-[120px] truncate">
                                        {record.category === 'POSTPONE' ? record.homework?.title : record.meeting?.title || '--'}
                                    </span>
                                </Space>
                            </div>

                            <div className="flex items-center gap-3 mb-4">
                                <Avatar
                                    src={record.owner?.avatar_url}
                                    icon={<UserOutlined />}
                                    className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm shrink-0"
                                    size="large"
                                />
                                <div className="flex flex-col min-w-0 flex-1">
                                    <Text strong className="truncate text-base">
                                        {record.owner?.name || (record.created_by ? `#${record.created_by}` : 'N/A')}
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
                                    title="Xóa đơn này?"
                                    onConfirm={() => onDelete(record.id)}
                                    disabled={!canDelete}
                                    okText="Xóa"
                                    cancelText="Hủy"
                                >
                                    <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete}>
                                        Xóa
                                    </Button>
                                </Popconfirm>
                            </div>
                        </Card>
                    </List.Item>
                )}
            />
        </div>
    );
};
