import {
    DeleteOutlined,
    EditOutlined,
    MailOutlined,
    PhoneOutlined,
    UserOutlined,
} from '@ant-design/icons';
import { Avatar, Badge, Button, Card, List, Popconfirm, Space, Tag, Typography } from 'antd';
import { UserStatus, type UserResponse } from '../types/user.types';

const { Text } = Typography;

interface UserMobileListProps {
    filteredUsers: UserResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onNavigate: (userId: number) => void;
    onEdit: (user: UserResponse) => void;
    onDelete: (id: number) => void;
}

export const UserMobileList = ({
    filteredUsers,
    isLoading,
    canUpdate,
    canDelete,
    onNavigate,
    onEdit,
    onDelete,
}: UserMobileListProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={filteredUsers}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 mb-4! border-0!" onClick={() => onNavigate(record.id)}>
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex flex-wrap gap-1">
                                {record.role_names && record.role_names.length > 0 ? (
                                    record.role_names.map((rn) => (
                                        <Tag
                                            key={rn}
                                            color={rn === 'admin' ? 'volcano' : rn === 'leader' ? 'blue' : 'green'}
                                            className="uppercase font-bold m-0 px-3 rounded-full"
                                        >
                                            {rn}
                                        </Tag>
                                    ))
                                ) : (
                                    <Tag className="uppercase font-bold m-0 px-3 rounded-full">NO ROLE</Tag>
                                )}
                            </div>
                            <Badge
                                status={record.status === UserStatus.ACTIVE ? 'success' : 'error'}
                                text={
                                    <span
                                        className={
                                            record.status === UserStatus.ACTIVE
                                                ? 'text-green-600 font-medium'
                                                : 'text-red-600 font-medium'
                                        }
                                    >
                                        {record.status}
                                    </span>
                                }
                            />
                        </div>

                        <div className="flex items-center gap-3 mb-4">
                            <Avatar
                                size={52}
                                src={record.avatar_url}
                                icon={<UserOutlined />}
                                className="bg-linear-to-br from-[#4f46e5] to-[#7c3aed] shrink-0 shadow-sm"
                            />
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="truncate text-base">{record.name}</Text>
                                <div className="flex items-center gap-1.5 text-gray-400">
                                    <MailOutlined className="text-xs" />
                                    <Text type="secondary" className="text-xs truncate">{record.email}</Text>
                                </div>
                            </div>
                        </div>

                        <div
                            role="presentation"
                            className="flex justify-between items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3 gap-2"
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => e.stopPropagation()}
                        >
                            <Space>
                                <PhoneOutlined className="text-gray-400" />
                                <Text className="text-xs">{record.phone_number || 'No phone'}</Text>
                            </Space>
                            <Space onClick={(e) => e.stopPropagation()}>
                                <Button
                                    icon={<EditOutlined />}
                                    size="small"
                                    onClick={() => onEdit(record)}
                                    disabled={!canUpdate}
                                >
                                    Sửa
                                </Button>
                                <Popconfirm
                                    title="Xóa thành viên này?"
                                    onConfirm={() => onDelete(record.id)}
                                    disabled={!canDelete}
                                    okText="Xóa"
                                    cancelText="Hủy"
                                >
                                    <Button
                                        icon={<DeleteOutlined />}
                                        size="small"
                                        danger
                                        disabled={!canDelete}
                                    />
                                </Popconfirm>
                            </Space>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);
