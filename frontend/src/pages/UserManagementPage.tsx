import { useState, useMemo } from 'react';
import {
    Table,
    Button,
    Card,
    Tag,
    Space,
    Modal,
    Form,
    Input,
    message,
    Popconfirm,
    Typography,
    Select,
    Badge,
    Row,
    Col,
    Avatar
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    UserOutlined,
    LockOutlined,
    MailOutlined,
    PhoneOutlined,
    CheckCircleOutlined,
    StopOutlined,
    SearchOutlined,
    FilterOutlined,
    DiscordOutlined,
    PictureOutlined
} from '@ant-design/icons';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useRoles } from '@/hooks';
import { useAuth } from '../context/AuthContext';
import { UserPermission } from '../types/rbac.types';
import type { UserResponse } from '../types/user.types';

import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

const UserManagementPage = () => {
    const navigate = useNavigate();
    const { hasPermission } = useAuth();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
    const [form] = Form.useForm();

    // Search & Filter states
    const [searchText, setSearchText] = useState('');
    const [filterRole, setFilterRole] = useState<string | undefined>(undefined);
    const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);

    // TanStack Query hooks
    const { data: users = [], isLoading } = useUsers();
    const { data: roles = [] } = useRoles();
    const createUser = useCreateUser();
    const updateUser = useUpdateUser();
    const deleteUser = useDeleteUser();

    // Filtered users
    const filteredUsers = useMemo(() => {
        return users.filter(user => {
            // Search filter (name, email, phone)
            const matchSearch = searchText === '' ||
                user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.email?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.phone_number?.toLowerCase().includes(searchText.toLowerCase());

            // Role filter
            const matchRole = !filterRole || user.role_name === filterRole;

            // Status filter
            const matchStatus = !filterStatus || user.status === filterStatus;

            return matchSearch && matchRole && matchStatus;
        });
    }, [users, searchText, filterRole, filterStatus]);

    const canCreate = hasPermission(UserPermission.CREATE);
    const canUpdate = hasPermission(UserPermission.UPDATE);
    const canDelete = hasPermission(UserPermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingUser) {
                await updateUser.mutateAsync({ id: editingUser.id, data: values });
                message.success('User updated successfully');
            } else {
                await createUser.mutateAsync(values);
                message.success('User created successfully');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteUser.mutateAsync(id);
            message.success('User deleted successfully');
        } catch (error) {
            message.error('Delete failed');
        }
    };

    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: UserResponse) => (
                <Space>
                    <Avatar
                        src={record.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-[#4f46e5] to-[#7c3aed] flex items-center justify-center text-white shadow-sm"
                    />
                    <div>
                        <Text strong className="block">{record.name}</Text>
                        {record.discord_id && (
                            <Text type="secondary" className="text-[10px] flex items-center gap-1">
                                <DiscordOutlined className="text-indigo-400" />
                                {record.discord_id}
                            </Text>
                        )}
                    </div>
                </Space>
            ),
        },
        {
            title: 'Liên hệ',
            key: 'contact',
            render: (_: any, record: UserResponse) => (
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
            dataIndex: 'role_name',
            key: 'role',
            render: (role: string) => (
                <Tag color={role === 'admin' ? 'volcano' : role === 'leader' ? 'blue' : 'green'} className="uppercase font-bold min-w-[80px] text-center">
                    {role || 'NO ROLE'}
                </Tag>
            ),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Badge
                    status={status === 'active' ? 'success' : 'error'}
                    text={status === 'active' ? <Tag color="success">ACTIVE</Tag> : <Tag color="error">INACTIVE</Tag>}
                />
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            render: (_: any, record: UserResponse) => (
                <Space>
                    <Button
                        icon={<UserOutlined />}
                        onClick={() => navigate(`/dashboard/profile/${record.id}`)}
                        className="hover:text-indigo-500 hover:border-indigo-500"
                        title="Xem hồ sơ"
                    />
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingUser(record);
                            form.setFieldsValue(record);
                            setIsModalOpen(true);
                        }}
                        disabled={!canUpdate}
                        className="hover:text-blue-500 hover:border-blue-500"
                        title="Chỉnh sửa"
                    />
                    <Popconfirm
                        title="Xóa thành viên này?"
                        description="Hành động này không thể hoàn tác."
                        onConfirm={() => handleDelete(record.id)}
                        disabled={!canDelete}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} danger disabled={!canDelete} title="Xóa" />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div className="p-6">
            <Card className="shadow-sm border-gray-100 rounded-xl overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                    <Space>
                        <UserOutlined className="text-2xl text-[#4f46e5]" />
                        <Title level={3} className="!m-0">Quản lý Thành viên</Title>
                    </Space>
                    {canCreate && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingUser(null);
                                form.resetFields();
                                form.setFieldsValue({ status: 'active' });
                                setIsModalOpen(true);
                            }}
                            className="bg-linear-to-r from-[#667eea] to-[#764ba2] border-none shadow-md h-10 px-6"
                        >
                            Add New User
                        </Button>
                    )}
                </div>

                {/* Search & Filter Bar */}
                <Row gutter={16} className="mb-4">
                    <Col xs={24} sm={12} md={8}>
                        <Input
                            placeholder="Tìm kiếm theo tên, email, SĐT..."
                            prefix={<SearchOutlined className="text-gray-400" />}
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            allowClear
                            className="w-full"
                        />
                    </Col>
                    <Col xs={12} sm={6} md={4}>
                        <Select
                            placeholder="Vai trò"
                            value={filterRole}
                            onChange={setFilterRole}
                            allowClear
                            className="w-full"
                            suffixIcon={<FilterOutlined />}
                        >
                            {roles.map(role => (
                                <Option key={role.id} value={role.name}>
                                    {role.name.toUpperCase()}
                                </Option>
                            ))}
                        </Select>
                    </Col>
                    <Col xs={12} sm={6} md={4}>
                        <Select
                            placeholder="Trạng thái"
                            value={filterStatus}
                            onChange={setFilterStatus}
                            allowClear
                            className="w-full"
                            suffixIcon={<FilterOutlined />}
                        >
                            <Option value="active">Active</Option>
                            <Option value="inactive">Inactive</Option>
                        </Select>
                    </Col>
                    {(searchText || filterRole || filterStatus) && (
                        <Col>
                            <Button
                                onClick={() => {
                                    setSearchText('');
                                    setFilterRole(undefined);
                                    setFilterStatus(undefined);
                                }}
                            >
                                Xóa bộ lọc
                            </Button>
                        </Col>
                    )}
                </Row>

                {!canUpdate && (
                    <div className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100 flex items-center">
                        <LockOutlined className="text-yellow-600 mr-3 text-lg" />
                        <Text type="warning">
                            You have read-only access. You cannot create, edit, or delete users.
                        </Text>
                    </div>
                )}

                <Table
                    columns={columns}
                    dataSource={filteredUsers}
                    rowKey="id"
                    loading={isLoading}
                    className="border border-gray-100 rounded-lg custom-table"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            <Modal
                title={
                    <Space>
                        {editingUser ? <EditOutlined /> : <PlusOutlined />}
                        <span>{editingUser ? 'Edit User Information' : 'Create New User Account'}</span>
                    </Space>
                }
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                width={600}
                centered
                okText={editingUser ? 'Save Changes' : 'Create User'}
                confirmLoading={createUser.isPending || updateUser.isPending}
                destroyOnHidden
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-6">
                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="name" label="Full Name" rules={[{ required: true, message: 'Please input the full name!' }]}>
                            <Input prefix={<UserOutlined className="text-gray-400" />} placeholder="John Doe" />
                        </Form.Item>
                        <Form.Item name="email" label="Email Address" rules={[{ required: true, type: 'email', message: 'Please input a valid email!' }]}>
                            <Input prefix={<MailOutlined className="text-gray-400" />} placeholder="john@example.com" disabled={!!editingUser} />
                        </Form.Item>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="phone_number" label="Phone Number">
                            <Input prefix={<PhoneOutlined className="text-gray-400" />} placeholder="+84 123 456 789" />
                        </Form.Item>
                        <Form.Item name="role_id" label="System Role" rules={[{ required: true, message: 'Please select a role!' }]}>
                            <Select placeholder="Select a role">
                                {roles.map(role => (
                                    <Option key={role.id} value={role.id}>
                                        <Tag color={role.name === 'admin' ? 'volcano' : role.name === 'leader' ? 'blue' : 'green'}>
                                            {role.name.toUpperCase()}
                                        </Tag>
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="status" label="Account Status" rules={[{ required: true }]}>
                            <Select>
                                <Option value="active">
                                    <Space><CheckCircleOutlined className="text-green-500" />Active</Space>
                                </Option>
                                <Option value="inactive">
                                    <Space><StopOutlined className="text-red-500" />Inactive</Space>
                                </Option>
                            </Select>
                        </Form.Item>
                        <Form.Item name="discord_id" label="Discord ID">
                            <Input prefix={<DiscordOutlined className="text-gray-400" />} placeholder="123456789" />
                        </Form.Item>
                    </div>

                    <Form.Item name="avatar_url" label="Avatar URL">
                        <Input prefix={<PictureOutlined className="text-gray-400" />} placeholder="https://example.com/avatar.jpg" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default UserManagementPage;
