import React from 'react';
import { Space, Typography } from 'antd';
import { MailOutlined, PhoneOutlined } from '@ant-design/icons';
import type { UserResponse } from '@/features/users/types/user.types';

const { Text } = Typography;

interface ProfileInfoTabProps {
    user: UserResponse;
}

export const ProfileInfoTab: React.FC<ProfileInfoTabProps> = ({ user }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
            <Space direction="vertical" size="large" className="w-full">
                <div>
                    <Text type="secondary" className="text-xs uppercase font-bold tracking-wider block mb-2">
                        Thông tin liên hệ
                    </Text>
                    <Space direction="vertical" className="w-full">
                        <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-50">
                            <MailOutlined className="text-indigo-500" />
                            <Text className="break-all">{user.email}</Text>
                        </div>
                        <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-50">
                            <PhoneOutlined className="text-indigo-500" />
                            <Text>{user.phone_number || 'Chưa cập nhật số điện thoại'}</Text>
                        </div>
                    </Space>
                </div>
            </Space>
        </div>
    );
};

export default ProfileInfoTab;
