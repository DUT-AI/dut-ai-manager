import React from 'react';
import { Space, Typography } from 'antd';

const { Text } = Typography;

export interface UserDisplayRecord {
    user_name?: string;
    user?: { name?: string; avatar_url?: string };
    owner?: { name?: string; avatar_url?: string };
    creator?: { name?: string; avatar_url?: string };
    [key: string]: unknown;
}

interface UserDisplayProps {
    record?: UserDisplayRecord | null;
    label?: string;
}

export const UserDisplay: React.FC<UserDisplayProps> = ({ record, label }) => {
    if (!record) return null;
    const name = record.user_name || record.user?.name || record.owner?.name || record.creator?.name || '--';
    const avatar = record.owner?.avatar_url || record.user?.avatar_url || record.creator?.avatar_url;

    return (
        <Space>
            {avatar ? (
                <img
                    src={avatar}
                    alt={name}
                    className="w-8 h-8 rounded-full object-cover border border-gray-100 shadow-sm"
                    onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`;
                    }}
                />
            ) : (
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 border border-gray-200">
                    {name.charAt(0).toUpperCase()}
                </div>
            )}
            <div className="flex flex-col">
                {label && <Text type="secondary" className="text-[10px] uppercase tracking-wider">{label}</Text>}
                <Text strong className="text-sm">{name}</Text>
            </div>
        </Space>
    );
};

export default UserDisplay;
