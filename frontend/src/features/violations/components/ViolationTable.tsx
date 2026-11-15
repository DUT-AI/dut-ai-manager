import { Table, Space, Avatar, Typography, Button, Popconfirm } from 'antd';
import { UserOutlined, CalendarOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { TablePaginationConfig } from 'antd';
import type { ViolationResponse } from '@/features/violations/types/violation.types';

const { Title, Text } = Typography;

interface ViolationTableProps {
    violations: ViolationResponse[];
    isLoading: boolean;
    paginationProps?: TablePaginationConfig;
    canUpdate: boolean;
    canDelete: boolean;
    selectedRowKeys?: number[];
    onSelectionChange?: (keys: number[]) => void;
    onEdit: (item: ViolationResponse) => void;
    onDelete: (id: number) => void;
    onRowClick: (item: ViolationResponse) => void;
}

const ViolationTable = ({
    violations,
    isLoading,
    paginationProps,
    canUpdate,
    canDelete,
    selectedRowKeys = [],
    onSelectionChange,
    onEdit,
    onDelete,
    onRowClick
}: ViolationTableProps) => {
    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            width: 240,
            render: (_: unknown, record: ViolationResponse) => (
                <Space>
                    <Avatar
                        src={record.owner?.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-red-500 to-orange-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Title level={5} className="!mb-0 text-sm whitespace-nowrap">{record.owner?.name || 'Unknown'}</Title>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Lý do vi phạm',
            dataIndex: 'reason',
            key: 'reason',
            render: (reason: string) => (
                <div className="py-1">
                    <Text className="block whitespace-pre-wrap break-words text-gray-700 leading-relaxed font-normal">
                        {reason}
                    </Text>
                </div>
            ),
        },
        {
            title: 'Thời gian',
            dataIndex: 'date',
            key: 'date',
            width: 220,
            render: (date: string) => (
                <Space className="whitespace-nowrap text-gray-600">
                    <CalendarOutlined className="text-gray-400" />
                    <Text>{dayjs(date).format('DD/MM/YYYY HH:mm')}</Text>
                </Space>
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 140,
            align: 'center' as const,
            render: (_: unknown, record: ViolationResponse) => (
                <Space onClick={(e) => e.stopPropagation()}>
                    <Button
                        icon={<EditOutlined />}
                        size="small"
                        onClick={() => onEdit(record)}
                        disabled={!canUpdate}
                    />
                    <Popconfirm
                        title="Xóa vi phạm này?"
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

    const rowSelection = canDelete && onSelectionChange ? {
        selectedRowKeys,
        onChange: (keys: React.Key[]) => onSelectionChange(keys as number[]),
    } : undefined;

    return (
        <Table
            columns={columns}
            dataSource={violations}
            rowKey="id"
            loading={isLoading}
            rowSelection={rowSelection}
            className="border border-gray-100 rounded-lg custom-table cursor-pointer"
            pagination={paginationProps}
            onRow={(record) => ({
                onClick: () => onRowClick(record),
                style: { cursor: 'pointer' }
            })}
        />
    );
};

export default ViolationTable;
