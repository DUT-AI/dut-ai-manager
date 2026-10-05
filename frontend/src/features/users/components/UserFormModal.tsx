import { useEffect } from 'react';
import {
    CheckCircleOutlined,
    DiscordOutlined,
    EditOutlined,
    MailOutlined,
    PhoneOutlined,
    PlusOutlined,
    StopOutlined,
    UserOutlined,
} from '@ant-design/icons';
import { Form, Grid, Input, Modal, Select, Space, Tag } from 'antd';
import type { RoleResponse } from '@/features/rbac';
import { UserStatus, type UserResponse } from '../types/user.types';

const { Option } = Select;

interface UserFormModalProps {
    open: boolean;
    editingUser: UserResponse | null;
    roles: RoleResponse[];
    isSubmitting: boolean;
    onCancel: () => void;
    onSubmit: (values: Record<string, unknown>) => Promise<void>;
}

export const UserFormModal = ({
    open,
    editingUser,
    roles,
    isSubmitting,
    onCancel,
    onSubmit,
}: UserFormModalProps) => {
    const [form] = Form.useForm();
    const screens = Grid.useBreakpoint();

    useEffect(() => {
        if (open) {
            if (editingUser) {
                form.setFieldsValue(editingUser);
            } else {
                form.resetFields();
                form.setFieldsValue({ status: UserStatus.ACTIVE });
            }
        }
    }, [open, editingUser, form]);

    return (
        <Modal
            title={
                <Space>
                    {editingUser ? <EditOutlined /> : <PlusOutlined />}
                    <span>{editingUser ? 'Edit User Information' : 'Create New User Account'}</span>
                </Space>
            }
            open={open}
            onCancel={onCancel}
            onOk={() => form.submit()}
            width={screens.xs ? '100%' : 600}
            centered
            okText={editingUser ? 'Save Changes' : 'Create User'}
            confirmLoading={isSubmitting}
            destroyOnHidden
        >
            <Form form={form} layout="vertical" onFinish={onSubmit} className="mt-6">
                <div className="grid grid-cols-2 gap-4">
                    <Form.Item
                        name="name"
                        label="Full Name"
                        rules={[{ required: true, message: 'Please input the full name!' }]}
                    >
                        <Input prefix={<UserOutlined className="text-gray-400" />} placeholder="John Doe" />
                    </Form.Item>
                    <Form.Item
                        name="email"
                        label="Email Address"
                        rules={[{ required: true, type: 'email', message: 'Please input a valid email!' }]}
                    >
                        <Input
                            prefix={<MailOutlined className="text-gray-400" />}
                            placeholder="john@example.com"
                            disabled={!!editingUser}
                        />
                    </Form.Item>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Form.Item name="phone_number" label="Phone Number">
                        <Input prefix={<PhoneOutlined className="text-gray-400" />} placeholder="+84 123 456 789" />
                    </Form.Item>
                    <Form.Item
                        name="role_ids"
                        label="System Roles"
                        rules={[{ required: true, message: 'Please select at least one role!' }]}
                    >
                        <Select
                            mode="multiple"
                            placeholder="Select roles"
                            style={{ width: '100%' }}
                            optionFilterProp="label"
                            showSearch
                        >
                            {roles.map((role) => (
                                <Option key={role.id} value={role.id} label={role.name}>
                                    <Tag
                                        color={
                                            role.name === 'admin'
                                                ? 'volcano'
                                                : role.name === 'leader'
                                                ? 'blue'
                                                : 'green'
                                        }
                                        className="m-0"
                                    >
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
                            <Option value={UserStatus.ACTIVE}>
                                <Space>
                                    <CheckCircleOutlined className="text-green-500" />Active
                                </Space>
                            </Option>
                            <Option value={UserStatus.INACTIVE}>
                                <Space>
                                    <StopOutlined className="text-red-500" />Inactive
                                </Space>
                            </Option>
                        </Select>
                    </Form.Item>
                    <Form.Item name="discord_id" label="Discord ID">
                        <Input prefix={<DiscordOutlined className="text-gray-400" />} placeholder="123456789" />
                    </Form.Item>
                </div>
            </Form>
        </Modal>
    );
};
