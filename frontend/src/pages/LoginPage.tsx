import { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Flex, Modal } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { authService } from '../services/api/auth.service';
import { useAuth } from '../context/AuthContext';
import type { LoginRequest } from '../types/auth.types';
import logo from '../assets/logo.jpg';
import background from '../assets/background.png';

const { Title, Text } = Typography;

interface LoginPageProps {
    onLoginSuccess: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
    const { login } = useAuth();
    const [loading, setLoading] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);
    const [forgotLoading, setForgotLoading] = useState(false);
    const [forgotForm] = Form.useForm();

    const onFinish = async (values: LoginRequest) => {
        setLoading(true);
        try {
            const response = await authService.login(values);

            if (response.is_success && response.data) {
                await login();
                messageApi.success('Login successful!');
                onLoginSuccess();
            } else {
                messageApi.error(response.message);
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.message || 'Login failed. Please try again.';
            messageApi.error(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const onForgotFinish = async (values: { email: string }) => {
        setForgotLoading(true);
        try {
            const response = await authService.forgotPassword(values.email);
            if (response.is_success) {
                messageApi.success('Chúng tôi đã gửi mật khẩu mới vào email của bạn. Vui lòng kiểm tra!');
                setIsForgotModalOpen(false);
                forgotForm.resetFields();
            } else {
                messageApi.error(response.message || 'Có lỗi xảy ra khi khôi phục mật khẩu.');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.message || 'Có lỗi xảy ra khi khôi phục mật khẩu.';
            messageApi.error(errorMessage);
        } finally {
            setForgotLoading(false);
        }
    };

    return (
        <>
            {contextHolder}
            <div
                className="min-h-screen flex items-center justify-start p-5 md:pl-32"
                style={{
                    backgroundImage: `url(${background})`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    backgroundRepeat: 'no-repeat'
                }}
            >
                <Card
                    className="w-full max-w-[420px] rounded-2xl shadow-2xl transition-all duration-300 hover:shadow-3xl border-none backdrop-blur-sm bg-white/90"
                    styles={{
                        body: { padding: '40px' }
                    }}
                >
                    <Flex vertical gap="large" className="w-full">
                        <div className="text-center">
                            <div className="flex justify-center mb-4">
                                <img
                                    src={logo}
                                    alt="Logo"
                                    className="w-24 h-24 rounded-full object-cover shadow-lg animate-bounce-subtle"
                                />
                            </div>
                            <Title level={2} className="m-0 text-[#1a1a2e] font-bold tracking-tight">
                                Welcome Back
                            </Title>
                            <Text className="text-gray-500 font-medium mt-2 block">
                                Sign in to DUT AI Manager
                            </Text>
                        </div>

                        <Form
                            name="login"
                            onFinish={onFinish}
                            layout="vertical"
                            size="large"
                            requiredMark={false}
                            className="mt-4"
                        >
                            <Form.Item
                                name="email"
                                rules={[
                                    { required: true, message: 'Please enter your email' },
                                    { type: 'email', message: 'Please enter a valid email' },
                                ]}
                                className="mb-4"
                            >
                                <Input
                                    prefix={<UserOutlined className="text-[#667eea]" />}
                                    placeholder="Email"
                                    className="rounded-lg h-12 border-gray-200"
                                />
                            </Form.Item>

                            <Form.Item
                                name="password"
                                rules={[{ required: true, message: 'Please enter your password' }]}
                                className="mb-2"
                            >
                                <Input.Password
                                    prefix={<LockOutlined className="text-[#667eea]" />}
                                    placeholder="Password"
                                    className="rounded-lg h-12 border-gray-200"
                                />
                            </Form.Item>

                            <div style={{ textAlign: 'right', marginBottom: '24px' }}>
                                <Button
                                    type="link"
                                    onClick={() => setIsForgotModalOpen(true)}
                                    className="text-[#667eea] p-0 font-medium hover:text-[#764ba2]"
                                >
                                    Quên mật khẩu?
                                </Button>
                            </div>

                            <Form.Item className="mb-0">
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    loading={loading}
                                    block
                                    className="h-12 rounded-lg bg-linear-to-r from-[#667eea] to-[#764ba2] border-none text-base font-semibold shadow-md hover:opacity-90 transform transition hover:-translate-y-0.5 active:translate-y-0"
                                >
                                    {loading ? 'Signing in...' : 'Sign In'}
                                </Button>
                            </Form.Item>
                        </Form>
                    </Flex>
                </Card>
            </div>

            <Modal
                title={
                    <Title level={4} style={{ margin: 0, textAlign: 'center', color: '#1a1a2e' }}>
                        Khôi phục mật khẩu
                    </Title>
                }
                open={isForgotModalOpen}
                onCancel={() => {
                    setIsForgotModalOpen(false);
                    forgotForm.resetFields();
                }}
                footer={null}
                centered
                width={400}
            >
                <div style={{ padding: '12px 0' }}>
                    <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: '24px' }}>
                        Nhập email tài khoản của bạn. Hệ thống sẽ tạo mật khẩu mới và gửi trực tiếp qua email.
                    </Text>
                    <Form
                        form={forgotForm}
                        onFinish={onForgotFinish}
                        layout="vertical"
                        size="large"
                    >
                        <Form.Item
                            name="email"
                            rules={[
                                { required: true, message: 'Vui lòng nhập email!' },
                                { type: 'email', message: 'Email không hợp lệ!' },
                            ]}
                        >
                            <Input
                                prefix={<UserOutlined className="text-[#667eea]" />}
                                placeholder="Email tài khoản"
                                className="rounded-lg h-12 border-gray-200"
                            />
                        </Form.Item>

                        <Form.Item style={{ marginBottom: 0 }}>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={forgotLoading}
                                block
                                className="h-12 rounded-lg bg-linear-to-r from-[#667eea] to-[#764ba2] border-none text-base font-semibold shadow-md hover:opacity-90 transform transition hover:-translate-y-0.5"
                            >
                                Gửi yêu cầu
                            </Button>
                        </Form.Item>
                    </Form>
                </div>
            </Modal>
        </>
    );
};

export default LoginPage;
