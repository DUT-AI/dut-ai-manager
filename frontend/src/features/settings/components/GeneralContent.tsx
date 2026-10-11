import React, { useState } from 'react';
import { Card, Form, Input, Button, Avatar, Upload, Typography, Tag, message } from 'antd';
import { UserOutlined, DiscordOutlined, UploadOutlined, IdcardOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { useAuth } from '@/features/auth';
import { userService } from '@/features/users/services/user.service';
import { zaloService } from '@/features/robot/services/zalo.service';
import ZaloBotModal from './ZaloBotModal';

const { Title, Text } = Typography;

const itemVariants: Variants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
        opacity: 1,
        scale: 1,
        transition: { duration: 0.3, ease: 'easeOut' }
    }
};

export const GeneralContent: React.FC = () => {
    const { user, refreshUser } = useAuth();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [loadingBotCode, setLoadingBotCode] = useState(false);
    const [botModalVisible, setBotModalVisible] = useState(false);
    const [botBindCode, setBotBindCode] = useState('');

    const handleGenerateBotCode = async () => {
        try {
            setLoadingBotCode(true);
            const data = await zaloService.getBotBindCode();
            if (data.data?.bind_code) {
                setBotBindCode(data.data.bind_code);
                setBotModalVisible(true);
            } else {
                message.error('Không thể tạo mã liên kết Zalo Bot');
            }
        } catch (error: any) {
            message.error(error.message || 'Có lỗi xảy ra khi gọi Zalo Bot API');
        } finally {
            setLoadingBotCode(false);
        }
    };

    const handleAvatarUpload = async (info: { file: { status?: string; originFileObj?: File } }) => {
        if (info.file.status === 'uploading') {
            setUploading(true);
            return;
        }
        if (info.file.status === 'done' || info.file.originFileObj) {
            try {
                setUploading(true);
                if (info.file.originFileObj) {
                    await userService.updateAvatar(info.file.originFileObj);
                }
                message.success('Cập nhật ảnh đại diện thành công');
                await refreshUser();
            } catch {
                message.error('Lỗi khi upload ảnh');
            } finally {
                setUploading(false);
            }
        }
    };

    const onUpdateSettings = async (values: Record<string, unknown>) => {
        setLoading(true);
        try {
            const payload: import('@/features/users/types/user.types').UserSettingsUpdate = {
                discord_id: values.discord_id as string | undefined,
            };
            const card = typeof values.check_in_card_code === 'string' ? values.check_in_card_code.trim() : '';
            if (card) {
                payload.check_in_card_code = card;
            }
            await userService.updateSettings(payload);
            message.success('Cập nhật thông tin thành công');
            await refreshUser();
            form.setFieldsValue({ check_in_card_code: '' });
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Cập nhật thất bại');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <motion.div variants={itemVariants} className="w-full max-w-2xl">
                <Card
                    title={<><UserOutlined className="mr-2" />Thông tin cá nhân</>}
                    bordered={false}
                    className="shadow-sm rounded-xl"
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
                            customRequest={({ onSuccess }) => {
                                setTimeout(() => onSuccess?.('ok'), 0);
                            }}
                            onChange={handleAvatarUpload}
                        >
                            <Button icon={<UploadOutlined />} loading={uploading} className="rounded-lg">
                                Thay đổi ảnh đại diện
                            </Button>
                        </Upload>

                        <div className="mt-6 text-center">
                            <Title level={5} className="mb-0! text-lg">{user?.name}</Title>
                            <Text type="secondary" className="text-sm">{user?.email}</Text>
                            <div className="mt-3">
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 shadow-sm uppercase tracking-wider">
                                    {user?.role_names?.join(', ')?.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Zalo Bot Integration */}
                    <div className="mb-6">
                        <Text type="secondary" className="text-xs uppercase font-bold tracking-wider block mb-2">
                            Liên kết dịch vụ
                        </Text>
                        <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-100">
                            <div className="flex items-center gap-3">
                                <Avatar src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/120px-Icon_of_Zalo.svg.png" size="small" />
                                <Text>Liên kết Zalo (Chatbot <Tag color="green" className="ml-1 border-none shadow-sm rounded-md">Miễn phí</Tag>)</Text>
                            </div>
                            {user?.zalo_bot_id ? (
                                <Tag color="green">Đã liên kết</Tag>
                            ) : (
                                <Button type="primary" size="small" className="bg-[#0068ff]" onClick={handleGenerateBotCode} loading={loadingBotCode}>Lấy mã</Button>
                            )}
                        </div>
                    </div>

                    {/* Use key to reinitialize form when user data changes after refresh */}
                    <Form
                        key={`${user?.discord_id ?? 'nd'}-${user?.check_in_card_code ? 'card-y' : 'card-n'}`}
                        form={form}
                        layout="vertical"
                        onFinish={onUpdateSettings}
                        initialValues={{ discord_id: user?.discord_id, check_in_card_code: '' }}
                    >
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

                        <Form.Item
                            label="Mã thẻ check-in"
                            tooltip="Mã duy nhất dùng khi điểm danh. Sau khi lưu, mã không hiển thị lại trên giao diện."
                        >
                            {user?.check_in_card_code_configured ? (
                                <Text type="secondary" className="block mb-2">
                                    Mã thẻ đã được lưu. Để đổi mã, nhập mã mới bên dưới (mã cũ sẽ bị thay thế).
                                </Text>
                            ) : (
                                <Text type="secondary" className="block mb-2">
                                    Chưa có mã. Nhập mã thẻ của bạn (mỗi tài khoản một mã, không trùng).
                                </Text>
                            )}
                            <Form.Item
                                name="check_in_card_code"
                                noStyle
                                rules={[
                                    { max: 64, message: 'Tối đa 64 ký tự' },
                                ]}
                            >
                                <Input.Password
                                    prefix={<IdcardOutlined className="text-gray-400" />}
                                    placeholder="Nhập mã thẻ (chỉ gửi khi thêm hoặc đổi mã)"
                                    size="large"
                                    className="rounded-lg"
                                    maxLength={64}
                                    autoComplete="off"
                                />
                            </Form.Item>
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
            </motion.div>

            <ZaloBotModal
                open={botModalVisible}
                bindCode={botBindCode}
                onClose={() => setBotModalVisible(false)}
            />
        </>
    );
};

export default GeneralContent;
