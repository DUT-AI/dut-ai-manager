import { Table, Space, Avatar, Typography, Button, Popconfirm } from 'antd';
import { UserOutlined, CalendarOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ViolationResponse } from '@/types/activity.types';

const { Title, Text } = Typography;

interface ViolationTableProps {
    violations: ViolationResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onEdit: (item: ViolationResponse) => void;
    onDelete: (id: number) => void;
    onRowClick: (item: ViolationResponse) => void;
}

const ViolationTable = ({
    violations,
    isLoading,
    canUpdate,
    canDelete,
    onEdit,
    onDelete,
    onRowClick
}: ViolationTableProps) => {
    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: ViolationResponse) => (
                <Space>
                    <Avatar
                        src={record.owner?.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-red-500 to-orange-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Title level={5} className="!mb-0 text-sm">{record.owner?.name || 'Unknown'}</Title>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Lý do vi phạm',
            dataIndex: 'reason',
            key: 'reason',
            render: (reason: string) => (
                <Text className="max-w-[300px] block truncate" title={reason}>{reason}</Text>
            ),
        },
        {
            title: 'Thời gian',
            dataIndex: 'date',
            key: 'date',
            render: (date: string) => (
                <Space>
                    <CalendarOutlined className="text-gray-400" />
                    <Text>{dayjs(date).format('DD/MM/YYYY HH:mm')}</Text>
                </Space>
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 120,
            render: (_: any, record: ViolationResponse) => (
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

    return (
        <Table
            columns={columns}
            dataSource={violations}
            rowKey="id"
            loading={isLoading}
            className="border border-gray-100 rounded-lg custom-table cursor-pointer"
            pagination={{ pageSize: 10 }}
            onRow={(record) => ({
                onClick: () => onRowClick(record),
                style: { cursor: 'pointer' }
            })}
        />
    );
};

export default ViolationTable;
