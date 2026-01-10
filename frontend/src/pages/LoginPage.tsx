import { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Flex } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { authService } from '../services/api/auth.service';
import { useAuth } from '../context/AuthContext';
import type { LoginRequest } from '../types/auth.types';

const { Title, Text } = Typography;

interface LoginPageProps {
    onLoginSuccess: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
    const { login } = useAuth();
    const [loading, setLoading] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();

    const onFinish = async (values: LoginRequest) => {
        setLoading(true);
        try {
            const response = await authService.login(values);

            if (response.is_success && response.data) {
                const { access_token, refresh_token } = response.data;
                await login(access_token, refresh_token);
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

    return (
        <>
            {contextHolder}
            <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-[#667eea] to-[#764ba2] p-5">
                <Card
                    className="w-full max-w-[420px] rounded-2xl shadow-2xl transition-all duration-300 hover:shadow-3xl border-none"
                    styles={{
                        body: { padding: '40px' }
                    }}
                >
                    <Flex vertical gap="large" className="w-full">
                        <div className="text-center">
                            <div className="w-20 h-20 rounded-full bg-linear-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center mx-auto mb-4 shadow-lg animate-bounce-subtle">
                                <LoginOutlined className="text-[36px] text-white" />
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
                                className="mb-6"
                            >
                                <Input.Password
                                    prefix={<LockOutlined className="text-[#667eea]" />}
                                    placeholder="Password"
                                    className="rounded-lg h-12 border-gray-200"
                                />
                            </Form.Item>

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
        </>
    );
};

export default LoginPage;
