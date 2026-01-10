import React, { useState } from 'react';
import { Layout, Menu, Typography, Form, Input, Button, Card, message, theme } from 'antd';
import { LockOutlined, UserOutlined, SettingOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { authService } from '@/services/api/auth.service';

const { Content, Sider } = Layout;
const { Title, Text } = Typography;

export const SettingsPage: React.FC = () => {
    const [activeKey, setActiveKey] = useState('password');
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    const { token } = theme.useToken();

    const onChangePassword = async (values: any) => {
        setLoading(true);
        try {
            await authService.changePassword({
                old_password: values.old_password,
                new_password: values.new_password,
                confirm_password: values.confirm_password,
            });
            message.success('Đổi mật khẩu thành công');
            form.resetFields();
        } catch (error: any) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const renderPasswordContent = () => (
        <Card
            title={<><LockOutlined className="mr-2" />Đổi mật khẩu</>}
            bordered={false}
            className="shadow-sm w-full max-w-2xl"
        >
            <Form form={form} layout="vertical" onFinish={onChangePassword} className="mt-4">
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
            title={<><SettingOutlined className="mr-2" />Cài đặt chung</>}
            bordered={false}
            className="shadow-sm w-full max-w-2xl"
        >
            <div className="text-center py-12">
                <div className="bg-gray-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <SettingOutlined className="text-2xl text-gray-400" />
                </div>
                <Text type="secondary">Các tính năng cài đặt chung đang được phát triển.</Text>
            </div>
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
                                label: 'Chung',
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
