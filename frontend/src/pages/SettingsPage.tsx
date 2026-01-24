import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Form, Input, Button, Card, message, Avatar, Upload } from 'antd';
import { LockOutlined, SettingOutlined, SafetyCertificateOutlined, UserOutlined, DiscordOutlined, UploadOutlined } from '@ant-design/icons';
import { authService } from '@/services/api/auth.service';
import { userService } from '@/services/api/user.service';
import { useAuth } from '@/context/AuthContext';

const { Content, Sider } = Layout;
const { Title, Text } = Typography;

export const SettingsPage: React.FC = () => {
    const { user, refreshUser } = useAuth();
    const [activeKey, setActiveKey] = useState('general');
    const [passwordForm] = Form.useForm();
    const [generalForm] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);

    useEffect(() => {
        if (user) {
            generalForm.setFieldsValue({
                discord_id: user.discord_id,
            });
        }
    }, [user, generalForm]);

    const onChangePassword = async (values: any) => {
        setLoading(true);
        try {
            await authService.changePassword({
                old_password: values.old_password,
                new_password: values.new_password,
                confirm_password: values.confirm_password,
            });
            message.success('Đổi mật khẩu thành công');
            passwordForm.resetFields();
        } catch (error: any) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const onUpdateSettings = async (values: any) => {
        setLoading(true);
        try {
            await userService.updateSettings(values);
            message.success('Cập nhật thông tin thành công');
            await refreshUser();
        } catch (error: any) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    const handleAvatarUpload = async (info: any) => {
        if (info.file.status === 'uploading') {
            setUploading(true);
            return;
        }
        if (info.file.status === 'done' || info.file.originFileObj) {
            try {
                setUploading(true);
                await userService.updateAvatar(info.file.originFileObj);
                message.success('Cập nhật ảnh đại diện thành công');
                await refreshUser();
            } catch (error) {
                message.error('Lỗi khi upload ảnh');
            } finally {
                setUploading(false);
            }
        }
    };

    const renderPasswordContent = () => (
        <Card
            title={<><LockOutlined className="mr-2" />Đổi mật khẩu</>}
            bordered={false}
            className="shadow-sm w-full max-w-2xl"
        >
            <Form form={passwordForm} layout="vertical" onFinish={onChangePassword} className="mt-4">
                <Form.Item
                    name="old_password"
                    label="Mật khẩu hiện tại"
                    rules={[{ required: true, message: 'Vui lòng nhập mật khẩu cũ' }]}
                >
                    <Input.Password prefix={<LockOutlined className="text-gray-400" />} placeholder="Nhập mật khẩu hiện tại" size="large" />
                </Form.Item>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Form.Item
                        name="new_password"
                        label="Mật khẩu mới"
                        rules={[
                            { required: true, message: 'Vui lòng nhập mật khẩu mới' },
                            { min: 6, message: 'Tối thiểu 6 ký tự' }
                        ]}
                    >
                        <Input.Password prefix={<SafetyCertificateOutlined className="text-gray-400" />} placeholder="Mật khẩu mới" size="large" />
                    </Form.Item>
                    <Form.Item
                        name="confirm_password"
                        label="Xác nhận mật khẩu"
                        dependencies={['new_password']}
                        rules={[
                            { required: true, message: 'Vui lòng xác nhận mật khẩu' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('new_password') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error('Mật khẩu không khớp!'));
                                },
                            }),
                        ]}
                    >
                        <Input.Password prefix={<SafetyCertificateOutlined className="text-gray-400" />} placeholder="Xác nhận mật khẩu" size="large" />
                    </Form.Item>
                </div>
                <Form.Item className="mb-0 mt-2">
                    <div className="flex justify-end">
                        <Button type="primary" htmlType="submit" loading={loading} size="large" className="bg-indigo-600 px-8">
                            Cập nhật mật khẩu
                        </Button>
                    </div>
                </Form.Item>
            </Form>
        </Card>
    );

    const renderGeneralContent = () => (
        <Card
            title={<><UserOutlined className="mr-2" />Thông tin cá nhân</>}
            bordered={false}
            className="shadow-sm w-full max-w-2xl"
        >
            <div className="flex flex-col items-center mb-10 bg-gray-50 p-8 rounded-2xl border border-gray-100">
                <Avatar
                    size={100}
                    src={user?.avatar_url}
                    icon={<UserOutlined />}
                    className="shadow-xl border-4 border-white mb-6"
                />

                <Upload
                    showUploadList={false}
                    beforeUpload={(file) => {
                        const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
                        if (!isJpgOrPng) {
                            message.error('Bạn chỉ có thể upload file JPG/PNG!');
                        }
                        const isLt2M = file.size / 1024 / 1024 < 2;
                        if (!isLt2M) {
                            message.error('Ảnh phải nhỏ hơn 2MB!');
                        }
                        return isJpgOrPng && isLt2M;
                    }}
                    customRequest={({ file, onSuccess }: any) => {
                        setTimeout(() => onSuccess("ok"), 0);
                    }}
                    onChange={handleAvatarUpload}
                >
                    <Button icon={<UploadOutlined />} loading={uploading}>
                        Thay đổi ảnh đại diện
                    </Button>
                </Upload>

                <div className="mt-6 text-center">
                    <Title level={5} className="!mb-0">{user?.name}</Title>
                    <Text type="secondary">{user?.email}</Text>
                    <div className="mt-2">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 shadow-sm">
                            {user?.role_name?.toUpperCase()}
                        </span>
                    </div>
                </div>
            </div>

            <Form form={generalForm} layout="vertical" onFinish={onUpdateSettings}>
                <Form.Item
                    name="discord_id"
                    label="Discord ID"
                    tooltip="ID người dùng Discord của bạn để nhận thông báo trực tiếp"
                >
                    <Input
                        prefix={<DiscordOutlined className="text-gray-400" />}
                        placeholder="Ví dụ: 123456789012345678"
                        size="large"
                    />
                </Form.Item>

                <Form.Item className="mb-0 mt-8">
                    <div className="flex justify-end">
                        <Button type="primary" htmlType="submit" loading={loading} size="large" className="bg-indigo-600 px-10 rounded-xl shadow-lg shadow-indigo-200">
                            Lưu thông tin
                        </Button>
                    </div>
                </Form.Item>
            </Form>
        </Card>
    );

    const renderContent = () => {
        switch (activeKey) {
            case 'password': return renderPasswordContent();
            case 'general': return renderGeneralContent();
            default: return null;
        }
    };

    return (
        <div className="absolute inset-0 bg-[#f8fafc]">
            <Layout className="bg-transparent h-full">
                <Sider
                    width={260}
                    theme="light"
                    className="bg-white border-r border-gray-200 h-full overflow-y-auto"
                >
                    <div className="p-6 border-b border-gray-100">
                        <Title level={4} className="!mb-1">Cài đặt</Title>
                        <Text type="secondary" className="text-xs">Quản lý tài khoản của bạn</Text>
                    </div>
                    <Menu
                        mode="inline"
                        selectedKeys={[activeKey]}
                        onClick={(e) => setActiveKey(e.key)}
                        className="border-none mt-2 px-2"
                        items={[
                            {
                                key: 'general',
                                icon: <SettingOutlined />,
                                label: 'Tài khoản',
                                className: 'mb-1 rounded-lg'
                            },
                            { type: 'divider' },
                            {
                                key: 'password',
                                icon: <LockOutlined />,
                                label: 'Bảo mật & Mật khẩu',
                                className: 'mt-1 rounded-lg'
                            },
                        ]}
                    />
                </Sider>
                <Content className="p-8 overflow-y-auto bg-gray-50 flex justify-center items-start">
                    {renderContent()}
                </Content>
            </Layout>
        </div>
    );
};
