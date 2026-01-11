import { useState, useEffect } from 'react';
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
    Badge
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
    StopOutlined
} from '@ant-design/icons';
import { userService } from '../services/api/user.service';
import { rbacService } from '../services/api/rbac.service';
import { useAuth } from '../context/AuthContext';
import { UserPermission } from '../types/rbac.types';
import type { UserResponse } from '../types/user.types';
import type { RoleResponse } from '../types/rbac.types';

import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

const UserManagementPage = () => {
    const navigate = useNavigate();
    const { hasPermission } = useAuth();
    const [users, setUsers] = useState<UserResponse[]>([]);
    const [roles, setRoles] = useState<RoleResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<UserResponse | null>(null);
    const [form] = Form.useForm();

    const canCreate = hasPermission(UserPermission.CREATE);
    const canUpdate = hasPermission(UserPermission.UPDATE);
    const canDelete = hasPermission(UserPermission.DELETE);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [usersRes, rolesRes] = await Promise.all([
                userService.getUsers(),
                rbacService.getRoles()
            ]);
            if (usersRes.is_success) setUsers(usersRes.data || []);
            if (rolesRes.is_success) setRoles(rolesRes.data || []);
        } catch (error) {
            message.error('Failed to fetch data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingUser) {
                const response = await userService.updateUser(editingUser.id, values);
                if (response.is_success) {
                    message.success('User updated successfully');
                } else {
                    message.error(response.message || 'Operation failed');
                    return;
                }
            } else {
                const response = await userService.createUser(values);
                if (response.is_success) {
                    message.success('User created successfully');
                } else {
                    message.error(response.message || 'Operation failed');
                    return;
                }
            }
            setIsModalOpen(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            message.error(error.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            const response = await userService.deleteUser(id);
            if (response.is_success) {
                message.success('User deleted successfully');
                fetchData();
            } else {
                message.error(response.message || 'Delete failed');
            }
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
                    <div className="w-10 h-10 rounded-full bg-linear-to-br from-[#4f46e5] to-[#7c3aed] flex items-center justify-center text-white shadow-sm">
                        <UserOutlined />
                    </div>
                    <div>
                        <Text strong className="block">{record.name}</Text>
                        <Text type="secondary" className="text-xs">ID: #{record.id}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Liên hệ',
            key: 'contact',
            render: (_: any, record: UserResponse) => (
                <div className="flex flex-col gap-1">
                    <div className="flex items-center text-xs">
                        <MailOutlined className="mr-2 text-gray-400" />
                        <Text>{record.email}</Text>
                    </div>
                    <div className="flex items-center text-xs">
                        <PhoneOutlined className="mr-2 text-gray-400" />
                        <Text>{record.phone_number || 'N/A'}</Text>
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
                    dataSource={users}
                    rowKey="id"
                    loading={loading}
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
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default UserManagementPage;
