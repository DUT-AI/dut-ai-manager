import {
    DeleteOutlined,
    EditOutlined,
    MailOutlined,
    PhoneOutlined,
    UserOutlined,
} from '@ant-design/icons';
import { Avatar, Badge, Button, Popconfirm, Space, Table, Tag, Typography } from 'antd';
import { UserStatus, type UserResponse } from '../types/user.types';

const { Text } = Typography;

interface UserTableProps {
    users: UserResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onNavigateProfile: (userId: number) => void;
    onEdit: (user: UserResponse) => void;
    onDelete: (userId: number) => void;
}

export const UserTable = ({
    users,
    isLoading,
    canUpdate,
    canDelete,
    onNavigateProfile,
    onEdit,
    onDelete,
}: UserTableProps) => {
    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            fixed: 'left' as const,
            render: (_: unknown, record: UserResponse) => (
                <Space>
                    <Avatar
                        src={record.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-[#4f46e5] to-[#7c3aed] flex items-center justify-center text-white shadow-sm"
                    />
                    <div>
                        <Text strong className="block">{record.name}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Liên hệ',
            key: 'contact',
            render: (_: unknown, record: UserResponse) => (
                <div className="flex flex-col gap-0.5">
                    <div className="flex items-center text-xs">
                        <MailOutlined className="mr-2 text-gray-400 text-[10px]" />
                        <Text className="text-xs">{record.email}</Text>
                    </div>
                    <div className="flex items-center text-xs">
                        <PhoneOutlined className="mr-2 text-gray-400 text-[10px]" />
                        <Text className="text-xs">{record.phone_number || 'N/A'}</Text>
                    </div>
                </div>
            ),
        },
        {
            title: 'Vai trò',
            dataIndex: 'role_names',
            key: 'role',
            render: (roles: string[]) => (
                <div className="flex flex-wrap gap-1">
                    {roles && roles.length > 0 ? (
                        roles.map((r) => (
                            <Tag
                                key={r}
                                color={r === 'admin' ? 'volcano' : r === 'leader' ? 'blue' : 'green'}
                                className="uppercase font-bold min-w-17.5 text-center m-0"
                            >
                                {r}
                            </Tag>
                        ))
                    ) : (
                        <Tag className="uppercase font-bold min-w-17.5 text-center m-0">NO ROLE</Tag>
                    )}
                </div>
            ),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: UserStatus) => (
                <Badge
                    status={status === UserStatus.ACTIVE ? 'success' : 'error'}
                    text={
                        status === UserStatus.ACTIVE ? (
                            <Tag color="success">ACTIVE</Tag>
                        ) : (
                            <Tag color="error">INACTIVE</Tag>
                        )
                    }
                />
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            fixed: 'right' as const,
            width: 150,
            render: (_: unknown, record: UserResponse) => (
                <Space>
                    <Button
                        icon={<UserOutlined />}
                        onClick={() => onNavigateProfile(record.id)}
                        className="hover:text-indigo-500 hover:border-indigo-500"
                        title="Xem hồ sơ"
                    />
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => onEdit(record)}
                        disabled={!canUpdate}
                        className="hover:text-blue-500 hover:border-blue-500"
                        title="Chỉnh sửa"
                    />
                    <Popconfirm
                        title="Xóa thành viên này?"
                        description="Hành động này không thể hoàn tác."
                        onConfirm={() => onDelete(record.id)}
                        disabled={!canDelete}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button
                            icon={<DeleteOutlined />}
                            danger
                            disabled={!canDelete}
                            title="Xóa"
                        />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            loading={isLoading}
            className="border border-gray-100 rounded-lg custom-table"
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1000 }}
        />
    );
};
