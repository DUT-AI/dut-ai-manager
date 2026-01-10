import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Typography,
    Avatar,
    Tag,
    Space,
    Skeleton,
    Button,
    message,
    Tabs,
    Table,
    DatePicker,
    Badge
} from 'antd';
import {
    UserOutlined,
    MailOutlined,
    PhoneOutlined,
    ArrowLeftOutlined,
    CalendarOutlined,
    SafetyCertificateOutlined,
    TrophyOutlined,
    WarningOutlined,
    FileProtectOutlined,
    FilterOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { userService } from '../services/api/user.service';
import { bonusPointService } from '../services/api/bonus-point.service';
import { violationService } from '../services/api/violation.service';
import { permissionService } from '../services/api/permission.service';

import type { UserResponse } from '../types/user.types';
import type { BonusPointResponse, ViolationResponse, PermissionRequestResponse } from '../types/activity.types';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

const ProfilePage = () => {
    const { userId } = useParams();
    const navigate = useNavigate();
    const [user, setUser] = useState<UserResponse | null>(null);
    const [loading, setLoading] = useState(true);

    // Filter state - default to current month/year
    const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());

    const [bonusPoints, setBonusPoints] = useState<BonusPointResponse[]>([]);
    const [violations, setViolations] = useState<ViolationResponse[]>([]);
    const [permissions, setPermissions] = useState<PermissionRequestResponse[]>([]);
    const [dataLoading, setDataLoading] = useState(false);

    // Fetch filtered data
    const fetchFilteredData = useCallback(async (uid: number, month: number, year: number) => {
        setDataLoading(true);
        try {
            const results = await Promise.allSettled([
                bonusPointService.getBonusPoints(uid, month, year),
                violationService.getViolations(0, 100, uid, month, year),
                permissionService.getPermissions(uid, month, year)
            ]);

            if (results[0].status === 'fulfilled') setBonusPoints(results[0].value.data || []);
            if (results[1].status === 'fulfilled') setViolations(results[1].value.data || []);
            if (results[2].status === 'fulfilled') setPermissions(results[2].value.data || []);
        } catch (error) {
            message.error('Failed to fetch filtered data');
        } finally {
            setDataLoading(false);
        }
    }, []);

    useEffect(() => {
        const fetchUser = async () => {
            if (!userId) return;
            const uid = parseInt(userId);

            try {
                const res = await userService.getUsers();
                if (res.data) {
                    const foundUser = res.data.find(u => u.id === uid);
                    if (foundUser) {
                        setUser(foundUser);
                        // Initial load with current month/year
                        await fetchFilteredData(uid, selectedDate.month() + 1, selectedDate.year());
                    } else {
                        message.error('User not found');
                        return;
                    }
                }
            } catch (error) {
                message.error('Failed to fetch user profile');
            } finally {
                setLoading(false);
            }
        };

        fetchUser();
    }, [userId]);

    // Handle date filter change
    const handleDateChange = async (date: Dayjs | null) => {
        if (!date || !userId) return;
        setSelectedDate(date);
        await fetchFilteredData(parseInt(userId), date.month() + 1, date.year());
    };

    const bonusColumns: ColumnsType<BonusPointResponse> = [
        { title: 'Lý do', dataIndex: 'reason', key: 'reason' },
        { title: 'Điểm', dataIndex: 'points', key: 'points', render: (val) => <Tag color="green">+{val}</Tag> },
        { title: 'Ngày', dataIndex: 'created_at', key: 'created_at', render: d => dayjs(d).format('DD/MM/YYYY') }
    ];

    const violationColumns: ColumnsType<ViolationResponse> = [
        { title: 'Lý do', dataIndex: 'reason', key: 'reason' },
        { title: 'Mức phạt', dataIndex: 'severity', key: 'severity', render: val => <Tag color="red">{val}</Tag> },
        { title: 'Ngày', dataIndex: 'created_at', key: 'created_at', render: d => dayjs(d).format('DD/MM/YYYY') }
    ];

    const permissionColumns: ColumnsType<PermissionRequestResponse> = [
        { title: 'Lý do', dataIndex: 'reason', key: 'reason' },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: val => {
                if (!val) return <Tag>N/A</Tag>;
                let color = 'default';
                if (val === 'approved') color = 'success';
                if (val === 'rejected') color = 'error';
                if (val === 'pending') color = 'warning';
                return <Tag color={color}>{val.toUpperCase()}</Tag>;
            }
        },
        { title: 'Ngày tạo', dataIndex: 'created_at', key: 'created_at', render: d => dayjs(d).format('DD/MM/YYYY') }
    ];

    // Filter component
    const FilterBar = () => (
        <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
            <FilterOutlined className="text-gray-500" />
            <Text type="secondary">Lọc theo tháng:</Text>
            <DatePicker
                picker="month"
                value={selectedDate}
                onChange={handleDateChange}
                format="MM/YYYY"
                allowClear={false}
                className="w-32"
            />
            <Text type="secondary" className="ml-auto text-xs">
                Hiển thị dữ liệu tháng {selectedDate.format('MM/YYYY')}
            </Text>
        </div>
    );

    if (loading) {
        return (
            <div className="p-8">
                <Card className="rounded-2xl shadow-sm border-gray-100">
                    <Skeleton active avatar paragraph={{ rows: 4 }} />
                </Card>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="p-8 flex flex-col items-center">
                <Text type="secondary">Không tìm thấy thông tin thành viên.</Text>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} className="mt-4">
                    Quay lại
                </Button>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate(-1)}
                type="text"
                className="mb-4 hover:bg-gray-100"
            >
                Quay lại
            </Button>

            <Card className="rounded-2xl shadow-sm border-gray-100 overflow-hidden">
                <div className="bg-linear-to-r from-[#4f46e5] to-[#7c3aed] h-32 -mx-6 -mt-6"></div>
                <div className="relative px-4">
                    <div className="absolute -top-12 left-0">
                        <Avatar
                            size={100}
                            icon={<UserOutlined />}
                            className="border-4 border-white bg-gray-100 text-[#4f46e5] shadow-md"
                        />
                    </div>
                    <div className="pt-16 pb-4">
                        <div className="flex justify-between items-start">
                            <div>
                                <Title level={2} className="!m-0">{user.name}</Title>
                                <Space direction="vertical" size={0} className="mt-1">
                                    <Text type="secondary" className="text-sm">#{user.id}</Text>
                                    <Tag color="blue" className="mt-2 uppercase font-bold">{user.role_name}</Tag>
                                </Space>
                            </div>
                            <Tag color={user.status === 'active' ? 'success' : 'error'} className="rounded-full px-4">
                                {user.status.toUpperCase()}
                            </Tag>
                        </div>
                    </div>
                </div>

                <Tabs defaultActiveKey="info" className="mt-4" items={[
                    {
                        key: 'info',
                        label: <span><UserOutlined /> Thông tin chung</span>,
                        children: (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
                                <Space direction="vertical" size="large" className="w-full">
                                    <div>
                                        <Text type="secondary" className="text-xs uppercase font-bold tracking-wider block mb-2">Thông tin liên hệ</Text>
                                        <Space direction="vertical" className="w-full">
                                            <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                <MailOutlined className="text-indigo-500" />
                                                <Text>{user.email}</Text>
                                            </div>
                                            <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                <PhoneOutlined className="text-indigo-500" />
                                                <Text>{user.phone_number || 'Chưa cập nhật số điện thoại'}</Text>
                                            </div>
                                        </Space>
                                    </div>
                                </Space>

                                <Space direction="vertical" size="large" className="w-full">
                                    <div>
                                        <Text type="secondary" className="text-xs uppercase font-bold tracking-wider block mb-2">Hoạt động hệ thống</Text>
                                        <Space direction="vertical" className="w-full">
                                            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                <Space>
                                                    <CalendarOutlined className="text-indigo-500" />
                                                    <Text>Lịch hoạt động</Text>
                                                </Space>
                                                <Button type="link" onClick={() => navigate('/dashboard/activities')}>Xem ngay</Button>
                                            </div>
                                            <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                <Space>
                                                    <SafetyCertificateOutlined className="text-indigo-500" />
                                                    <Text>Vai trò hiện tại</Text>
                                                </Space>
                                                <Tag color="purple">{user.role_name}</Tag>
                                            </div>
                                        </Space>
                                    </div>
                                </Space>
                            </div>
                        )
                    },
                    {
                        key: 'violations',
                        label: <Badge count={violations.length} size="small" offset={[8, 0]}><span><WarningOutlined /> Lỗi vi phạm</span></Badge>,
                        children: (
                            <>
                                <FilterBar />
                                <Table dataSource={violations} columns={violationColumns} rowKey="id" loading={dataLoading} pagination={{ pageSize: 10 }} />
                            </>
                        )
                    },
                    {
                        key: 'bonus',
                        label: <Badge count={bonusPoints.length} size="small" offset={[8, 0]}><span><TrophyOutlined /> Điểm cộng</span></Badge>,
                        children: (
                            <>
                                <FilterBar />
                                <Table dataSource={bonusPoints} columns={bonusColumns} rowKey="id" loading={dataLoading} pagination={{ pageSize: 10 }} />
                            </>
                        )
                    },
                    {
                        key: 'permissions',
                        label: <Badge count={permissions.length} size="small" offset={[8, 0]}><span><FileProtectOutlined /> Xin phép</span></Badge>,
                        children: (
                            <>
                                <FilterBar />
                                <Table dataSource={permissions} columns={permissionColumns} rowKey="id" loading={dataLoading} pagination={{ pageSize: 10 }} />
                            </>
                        )
                    }
                ]} />
            </Card>
        </div>
    );
};

export default ProfilePage;
