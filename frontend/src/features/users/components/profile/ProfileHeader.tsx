import React from 'react';
import { Avatar, Tag, Typography } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import type { UserResponse } from '@/features/users/types/user.types';
import { UserStatus } from '@/features/users/types/user.types';

const { Title } = Typography;

interface ProfileHeaderProps {
    user: UserResponse;
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({ user }) => {
    return (
        <div className="relative">
            <div className="bg-linear-to-r from-[#4f46e5] to-[#7c3aed] h-32 -mx-6 -mt-6"></div>
            <div className="relative px-4">
                <div className="absolute -top-12 left-0">
                    <Avatar
                        size={100}
                        src={user.avatar_url}
                        icon={<UserOutlined />}
                        className="border-4 border-white bg-gray-100 text-[#4f46e5] shadow-md"
                    />
                </div>
                <div className="pt-16 pb-4">
                    <div className="flex flex-col sm:flex-row justify-between items-start gap-2">
                        <div>
                            <Title level={2} className="m-0!">{user.name}</Title>
                            <div className="flex flex-wrap gap-1 mt-2">
                                {user.role_names?.map((rn) => (
                                    <Tag key={rn} color="blue" className="uppercase font-bold m-0">{rn}</Tag>
                                ))}
                            </div>
                        </div>
                        <Tag
                            color={user.status === UserStatus.ACTIVE ? 'success' : 'error'}
                            className="rounded-full px-4 sm:self-start"
                        >
                            {user.status}
                        </Tag>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfileHeader;
