import React from 'react';
import { Table, Space, Tag, Avatar, Typography, Button, Popconfirm } from 'antd';
import {
    UserOutlined,
    FileTextOutlined,
    ClockCircleOutlined,
    EditOutlined,
    DeleteOutlined,
} from '@ant-design/icons';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';
import { CATEGORY_COLORS, CATEGORY_LABELS } from './constants';

const { Text } = Typography;

interface PermissionTableProps {
    permissions: PermissionRequestResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onViewDetail: (item: PermissionRequestResponse) => void;
    onEdit: (item: PermissionRequestResponse) => void;
    onDelete: (id: number) => void;
}

export const PermissionTable: React.FC<PermissionTableProps> = ({
    permissions,
    isLoading,
    canUpdate,
    canDelete,
    onViewDetail,
    onEdit,
    onDelete,
}) => {
    const columns = [
        {
            title: 'Người tạo',
            key: 'creator',
            render: (_: any, record: PermissionRequestResponse) => (
                <Space>
                    <Avatar
                        src={record.owner?.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Text strong className="block">
                            {record.owner?.name || (record.created_by ? `#${record.created_by}` : 'N/A')}
                        </Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Loại phép',
            dataIndex: 'category',
            key: 'category',
            render: (category: string) => (
                <Tag color={CATEGORY_COLORS[category.toLowerCase()] || 'default'} className="font-medium px-3 rounded-full">
                    {CATEGORY_LABELS[category.toLowerCase()] || category}
                </Tag>
            ),
        },
        {
            title: 'Mục tiêu',
            key: 'target',
            render: (_: any, record: PermissionRequestResponse) => {
                if (record.category === 'POSTPONE' && record.homework) {
                    return (
                        <Space>
                            <FileTextOutlined className="text-indigo-400" />
                            <Text strong className="text-indigo-600">{record.homework.title}</Text>
                        </Space>
                    );
                }
                if ((record.category === 'ABSENCE' || record.category === 'LATE') && record.meeting) {
                    return (
                        <Space>
                            <ClockCircleOutlined className="text-purple-400" />
                            <Text strong className="text-purple-600">{record.meeting.title}</Text>
                        </Space>
                    );
                }
                return <Text type="secondary">--</Text>;
            },
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 120,
            render: (_: any, record: PermissionRequestResponse) => (
                <Space onClick={(e) => e.stopPropagation()}>
                    <Button
                        icon={<EditOutlined />}
                        size="small"
                        onClick={() => onEdit(record)}
                        disabled={!canUpdate}
                    />
                    <Popconfirm
                        title="Xóa đơn này?"
                        onConfirm={() => onDelete(record.id)}
                        disabled={!canDelete}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete} />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={permissions}
            rowKey="id"
            loading={isLoading}
            className="border border-gray-100 rounded-lg custom-table cursor-pointer"
            pagination={{ pageSize: 10 }}
            onRow={(record) => ({
                onClick: () => onViewDetail(record),
                style: { cursor: 'pointer' },
            })}
        />
    );
};
