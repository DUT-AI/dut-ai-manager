import React, { useState } from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { LockOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { authService } from '@/features/auth/services/auth.service';

const itemVariants: Variants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
        opacity: 1,
        scale: 1,
        transition: { duration: 0.3, ease: 'easeOut' }
    }
};

export const PasswordContent: React.FC = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    const onFinish = async (values: Record<string, unknown>) => {
        setLoading(true);
        try {
            await authService.changePassword({
                old_password: String(values.old_password || ''),
                new_password: String(values.new_password || ''),
                confirm_password: String(values.confirm_password || ''),
            });
            message.success('Đổi mật khẩu thành công');
            form.resetFields();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Đổi mật khẩu thất bại');
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div variants={itemVariants} className="w-full max-w-2xl">
            <Card
                title={<><LockOutlined className="mr-2" />Đổi mật khẩu</>}
                bordered={false}
                className="shadow-sm rounded-xl"
            >
                <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4">
                    <Form.Item
                        name="old_password"
                        label="Mật khẩu hiện tại"
                        rules={[{ required: true, message: 'Vui lòng nhập mật khẩu cũ' }]}
                    >
                        <Input.Password
                            prefix={<LockOutlined className="text-gray-400" />}
                            placeholder="Nhập mật khẩu hiện tại"
                            size="large"
                            className="rounded-lg"
                        />
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
                            <Input.Password
                                prefix={<SafetyCertificateOutlined className="text-gray-400" />}
                                placeholder="Mật khẩu mới"
                                size="large"
                                className="rounded-lg"
                            />
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
                            <Input.Password
                                prefix={<SafetyCertificateOutlined className="text-gray-400" />}
                                placeholder="Xác nhận mật khẩu"
                                size="large"
                                className="rounded-lg"
                            />
                        </Form.Item>
                    </div>
                    <Form.Item className="mb-0 mt-4">
                        <div className="flex justify-end">
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                                size="large"
                                className="w-full md:w-auto bg-indigo-600 px-8 rounded-lg font-semibold h-11"
                            >
                                Cập nhật mật khẩu
                            </Button>
                        </div>
                    </Form.Item>
                </Form>
            </Card>
        </motion.div>
    );
};

export default PasswordContent;
