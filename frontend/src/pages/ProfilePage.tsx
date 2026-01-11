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
    Badge,
    Modal,
    Descriptions
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

    // Detail modal states
    const [selectedViolation, setSelectedViolation] = useState<ViolationResponse | null>(null);
    const [selectedBonus, setSelectedBonus] = useState<BonusPointResponse | null>(null);
    const [selectedPermission, setSelectedPermission] = useState<PermissionRequestResponse | null>(null);

    // Helper: sort by created_at desc (newest first)
    const sortByDateDesc = <T extends { created_at: string }>(arr: T[]): T[] => {
        return [...arr].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf());
    };

    // Fetch filtered data
    const fetchFilteredData = useCallback(async (uid: number, month: number, year: number) => {
        setDataLoading(true);
        try {
            const results = await Promise.allSettled([
                bonusPointService.getBonusPoints(uid, month, year),
                violationService.getViolations(0, 100, uid, month, year),
                permissionService.getPermissions(uid, month, year)
            ]);

            if (results[0].status === 'fulfilled') setBonusPoints(sortByDateDesc(results[0].value.data || []));
            if (results[1].status === 'fulfilled') setViolations(sortByDateDesc(results[1].value.data || []));
            if (results[2].status === 'fulfilled') setPermissions(sortByDateDesc(results[2].value.data || []));
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
        { title: 'Lý do', dataIndex: 'reason', key: 'reason', ellipsis: true },
        { title: 'Điểm', dataIndex: 'points', key: 'points', width: 80, render: (val) => <Tag color="green">+{val}</Tag> },
        { title: 'Ngày', dataIndex: 'created_at', key: 'created_at', width: 120, render: d => dayjs(d).format('DD/MM/YYYY') }
    ];

    const violationColumns: ColumnsType<ViolationResponse> = [
        { title: 'Lý do', dataIndex: 'reason', key: 'reason', ellipsis: true },
        { title: 'Ngày vi phạm', dataIndex: 'date', key: 'date', width: 120, render: d => dayjs(d).format('DD/MM/YYYY') },
        { title: 'Ngày tạo', dataIndex: 'created_at', key: 'created_at', width: 120, render: d => dayjs(d).format('DD/MM/YYYY') }
    ];

    const permissionColumns: ColumnsType<PermissionRequestResponse> = [
        { title: 'Loại', dataIndex: 'category', key: 'category', width: 120 },
        { title: 'Nội dung', dataIndex: 'note', key: 'note', ellipsis: true },
        { title: 'Thời gian', key: 'time', width: 140, render: (_, r) => `${r.start_time} - ${r.end_time}` },
        { title: 'Ngày', dataIndex: 'date', key: 'date', width: 120, render: d => dayjs(d).format('DD/MM/YYYY') }
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
                                <Table
                                    dataSource={violations}
                                    columns={violationColumns}
                                    rowKey="id"
                                    loading={dataLoading}
                                    pagination={{ pageSize: 10 }}
                                    onRow={(record) => ({
                                        onClick: () => setSelectedViolation(record),
                                        className: 'cursor-pointer hover:bg-gray-50'
                                    })}
                                />
                            </>
                        )
                    },
                    {
                        key: 'bonus',
                        label: <Badge count={bonusPoints.length} size="small" offset={[8, 0]}><span><TrophyOutlined /> Điểm cộng</span></Badge>,
                        children: (
                            <>
                                <FilterBar />
                                <Table
                                    dataSource={bonusPoints}
                                    columns={bonusColumns}
                                    rowKey="id"
                                    loading={dataLoading}
                                    pagination={{ pageSize: 10 }}
                                    onRow={(record) => ({
                                        onClick: () => setSelectedBonus(record),
                                        className: 'cursor-pointer hover:bg-gray-50'
                                    })}
                                />
                            </>
                        )
                    },
                    {
                        key: 'permissions',
                        label: <Badge count={permissions.length} size="small" offset={[8, 0]}><span><FileProtectOutlined /> Xin phép</span></Badge>,
                        children: (
                            <>
                                <FilterBar />
                                <Table
                                    dataSource={permissions}
                                    columns={permissionColumns}
                                    rowKey="id"
                                    loading={dataLoading}
                                    pagination={{ pageSize: 10 }}
                                    onRow={(record) => ({
                                        onClick: () => setSelectedPermission(record),
                                        className: 'cursor-pointer hover:bg-gray-50'
                                    })}
                                />
                            </>
                        )
                    }
                ]} />
            </Card>

            {/* Detail Modals */}
            <Modal
                title={<><WarningOutlined className="text-red-500 mr-2" /> Chi tiết vi phạm</>}
                open={!!selectedViolation}
                onCancel={() => setSelectedViolation(null)}
                footer={null}
            >
                {selectedViolation && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Lý do">{selectedViolation.reason}</Descriptions.Item>
                        <Descriptions.Item label="Ngày vi phạm">
                            {dayjs(selectedViolation.date).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Người tạo">
                            {selectedViolation.creator_name || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedViolation.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>

            <Modal
                title={<><TrophyOutlined className="text-green-500 mr-2" /> Chi tiết điểm cộng</>}
                open={!!selectedBonus}
                onCancel={() => setSelectedBonus(null)}
                footer={null}
            >
                {selectedBonus && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Lý do">{selectedBonus.reason}</Descriptions.Item>
                        <Descriptions.Item label="Điểm cộng">
                            <Tag color="green">+{selectedBonus.points}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày">
                            {dayjs(selectedBonus.date).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedBonus.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>

            <Modal
                title={<><FileProtectOutlined className="text-blue-500 mr-2" /> Chi tiết đơn xin phép</>}
                open={!!selectedPermission}
                onCancel={() => setSelectedPermission(null)}
                footer={null}
            >
                {selectedPermission && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Loại">{selectedPermission.category}</Descriptions.Item>
                        <Descriptions.Item label="Nội dung">{selectedPermission.note}</Descriptions.Item>
                        <Descriptions.Item label="Thời gian">
                            {selectedPermission.start_time} - {selectedPermission.end_time}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày xin phép">
                            {dayjs(selectedPermission.date).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Người tạo">
                            {selectedPermission.creator_name || selectedPermission.user_name || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedPermission.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>
        </div>
    );
};

export default ProfilePage;
