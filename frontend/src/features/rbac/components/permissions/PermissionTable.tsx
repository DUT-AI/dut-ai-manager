import React from 'react';
import { Table, Space, Tag, Avatar, Typography, Button, Popconfirm, type TablePaginationConfig } from 'antd';
import {
    UserOutlined,
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
    pagination?: TablePaginationConfig | false;
    onViewDetail: (item: PermissionRequestResponse) => void;
    onEdit: (item: PermissionRequestResponse) => void;
    onDelete: (id: number) => void;
}

export const PermissionTable: React.FC<PermissionTableProps> = ({
    permissions,
    isLoading,
    canUpdate,
    canDelete,
    pagination,
    onViewDetail,
    onEdit,
    onDelete,
}) => {
    const columns = [
        {
            title: 'Người tạo',
            key: 'creator',
            render: (_: unknown, record: PermissionRequestResponse) => {
                const user = record.creator;
                return (
                    <Space>
                        <Avatar
                            src={user?.avatar_url}
                            icon={<UserOutlined />}
                            className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm"
                            size="small"
                        />
                        <div>
                            <Text strong className="block">
                                {user?.name || (record.created_by ? `#${record.created_by}` : 'N/A')}
                            </Text>
                        </div>
                    </Space>
                );
            },
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
            title: 'Thao tác',
            key: 'actions',
            width: 120,
            render: (_: unknown, record: PermissionRequestResponse) => (
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
            pagination={pagination !== undefined ? pagination : {
                defaultPageSize: 20,
                pageSizeOptions: ['10', '20', '50', '100'],
                showSizeChanger: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} của ${total} đơn phép`,
            }}
            onRow={(record) => ({
                onClick: () => onViewDetail(record),
                style: { cursor: 'pointer' },
            })}
        />
    );
};
