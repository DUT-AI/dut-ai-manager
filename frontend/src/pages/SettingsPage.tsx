import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Form, Input, Button, Card, message, Avatar, Upload, Grid } from 'antd';
import { LockOutlined, SettingOutlined, SafetyCertificateOutlined, UserOutlined, DiscordOutlined, UploadOutlined } from '@ant-design/icons';
import { authService } from '@/services/api/auth.service';
import { userService } from '@/services/api/user.service';
import { useAuth } from '@/context/AuthContext';

const { Content, Sider } = Layout;
const { Title, Text } = Typography;

export const SettingsPage: React.FC = () => {
    const { user, refreshUser } = useAuth();
    const screens = Grid.useBreakpoint();
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
            className="shadow-sm w-full max-w-2xl rounded-xl"
        >
            <Form form={passwordForm} layout="vertical" onFinish={onChangePassword} className="mt-4">
                <Form.Item
                    name="old_password"
                    label="Mật khẩu hiện tại"
                    rules={[{ required: true, message: 'Vui lòng nhập mật khẩu cũ' }]}
                >
                    <Input.Password prefix={<LockOutlined className="text-gray-400" />} placeholder="Nhập mật khẩu hiện tại" size="large" className="rounded-lg" />
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
                        <Input.Password prefix={<SafetyCertificateOutlined className="text-gray-400" />} placeholder="Mật khẩu mới" size="large" className="rounded-lg" />
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
                        <Input.Password prefix={<SafetyCertificateOutlined className="text-gray-400" />} placeholder="Xác nhận mật khẩu" size="large" className="rounded-lg" />
                    </Form.Item>
                </div>
                <Form.Item className="mb-0 mt-4">
                    <div className="flex justify-end">
                        <Button type="primary" htmlType="submit" loading={loading} size="large" className="w-full md:w-auto bg-indigo-600 px-8 rounded-lg font-semibold h-11">
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
            className="shadow-sm w-full max-w-2xl rounded-xl"
        >
            <div className="flex flex-col items-center mb-8 bg-gray-50 p-6 md:p-8 rounded-2xl border border-gray-100">
                <Avatar
                    size={80}
                    src={user?.avatar_url}
                    icon={<UserOutlined />}
                    className="shadow-lg border-4 border-white mb-6"
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
                    customRequest={({ onSuccess }: any) => {
                        setTimeout(() => onSuccess("ok"), 0);
                    }}
                    onChange={handleAvatarUpload}
                >
                    <Button icon={<UploadOutlined />} loading={uploading} className="rounded-lg">
                        Thay đổi ảnh đại diện
                    </Button>
                </Upload>

                <div className="mt-6 text-center">
                    <Title level={5} className="!mb-0 text-lg">{user?.name}</Title>
                    <Text type="secondary" className="text-sm">{user?.email}</Text>
                    <div className="mt-3">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 shadow-sm uppercase tracking-wider">
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
                        className="rounded-lg"
                    />
                </Form.Item>

                <Form.Item className="mb-0 mt-6">
                    <div className="flex justify-end">
                        <Button type="primary" htmlType="submit" loading={loading} size="large" className="w-full md:w-auto bg-indigo-600 px-10 rounded-xl shadow-lg shadow-indigo-100 font-semibold h-11">
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

    const menuItems = [
        {
            key: 'general',
            icon: <SettingOutlined />,
            label: 'Tài khoản',
        },
        {
            key: 'password',
            icon: <LockOutlined />,
            label: 'Bảo mật',
        },
    ];

    return (
        <div className={screens.md ? "absolute inset-0 bg-[#f8fafc]" : "bg-[#f8fafc] min-h-screen pb-10"}>
            <Layout className="bg-transparent h-full flex flex-col md:flex-row">
                {screens.md ? (
                    <Sider
                        width={260}
                        theme="light"
                        className="bg-white border-r border-gray-200 h-full overflow-y-auto shrink-0"
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
                            items={menuItems.map(item => ({
                                ...item,
                                className: 'rounded-lg mb-1'
                            }))}
                        />
                    </Sider>
                ) : (
                    <div className="bg-white border-b border-gray-200 sticky top-0 z-10 p-4">
                        <div className="mb-4">
                            <Title level={4} className="!mb-0">Cài đặt</Title>
                            <Text type="secondary" className="text-xs">Quản lý tài khoản cá nhân</Text>
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
                            {menuItems.map(item => (
                                <Button
                                    key={item.key}
                                    type={activeKey === item.key ? 'primary' : 'default'}
                                    icon={item.icon}
                                    onClick={() => setActiveKey(item.key)}
                                    className={`rounded-full shadow-none ${activeKey === item.key ? 'bg-indigo-600' : ''}`}
                                >
                                    {item.label}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}
                <Content className="p-4 md:p-8 overflow-y-auto bg-gray-50 flex justify-center items-start">
                    <div className="w-full flex justify-center">
                        {renderContent()}
                    </div>
                </Content>
            </Layout>
        </div>
    );
};

export default SettingsPage;
