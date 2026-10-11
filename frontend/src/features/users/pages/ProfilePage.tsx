import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Skeleton, Button, Tabs, Typography } from 'antd';
import {
    UserOutlined,
    ArrowLeftOutlined,
    WarningOutlined,
    TrophyOutlined,
    FileProtectOutlined
} from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { useUser } from '../hooks/useUsers';
import {
    ProfileHeader,
    ProfileInfoTab,
    ProfileViolationsTab,
    ProfileBonusPointsTab,
    ProfilePermissionsTab
} from '../components/profile';

const { Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' }
    }
};

export const ProfilePage: React.FC = () => {
    const { userId } = useParams();
    const navigate = useNavigate();
    const uid = userId ? parseInt(userId, 10) : undefined;

    const [activeTab, setActiveTab] = useState<"info" | "violations" | "bonus" | "permissions">('info');

    // Fetch user details
    const { data: user, isLoading: usersLoading } = useUser(uid ?? 0);

    if (usersLoading) {
        return (
            <div className="p-4 md:p-8">
                <Card className="rounded-2xl shadow-sm border-gray-100">
                    <Skeleton active avatar paragraph={{ rows: 4 }} />
                </Card>
            </div>
        );
    }

    if (!user || !uid) {
        return (
            <div className="p-4 md:p-8 flex flex-col items-center">
                <Text type="secondary">Không tìm thấy thông tin thành viên.</Text>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} className="mt-4">
                    Quay lại
                </Button>
            </div>
        );
    }

    const tabItems = [
        {
            key: 'info',
            label: <span><UserOutlined /> Thông tin chung</span>,
            children: <ProfileInfoTab user={user} />
        },
        {
            key: 'violations',
            label: <span><WarningOutlined /> Lỗi vi phạm</span>,
            children: <ProfileViolationsTab userId={uid} isActive={activeTab === 'violations'} />
        },
        {
            key: 'bonus',
            label: <span><TrophyOutlined /> Điểm cộng</span>,
            children: <ProfileBonusPointsTab userId={uid} isActive={activeTab === 'bonus'} />
        },
        {
            key: 'permissions',
            label: <span><FileProtectOutlined /> Xin phép</span>,
            children: <ProfilePermissionsTab userId={uid} isActive={activeTab === 'permissions'} />
        }
    ];

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-8 w-full"
        >
            <motion.div variants={itemVariants}>
                <Button
                    icon={<ArrowLeftOutlined />}
                    onClick={() => navigate(-1)}
                    type="text"
                    className="mb-4 hover:bg-gray-100"
                >
                    Quay lại
                </Button>
            </motion.div>

            <motion.div variants={itemVariants}>
                <Card className="rounded-2xl shadow-sm border-gray-100 overflow-hidden">
                    <ProfileHeader user={user} />
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        className="mt-4"
                        items={tabItems}
                    />
                </Card>
            </motion.div>
        </motion.div>
    );
};

export default ProfilePage;
