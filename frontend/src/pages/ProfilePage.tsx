import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Typography,
    Avatar,
    Tag,
    Space,
    Skeleton,
    Button,
    Tabs,
    Table,
    DatePicker,
    Badge,
    Modal,
    Descriptions,
    message
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
import { useUsers, useViolations, useBonusPoints, usePermissionRequests } from '@/hooks';
import { zaloService } from '@/services/api/zalo.service';

import type { BonusPointResponse, ViolationResponse, PermissionRequestResponse } from '../types/activity.types';
import type { ColumnsType } from 'antd/es/table';
import { motion, type Variants } from 'motion/react';

const { Title, Text } = Typography;

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
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

interface FilterBarProps {
    selectedDate: Dayjs;
    onChange: (date: Dayjs) => void;
}

const FilterBar = ({ selectedDate, onChange }: FilterBarProps) => (
    <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
        <FilterOutlined className="text-gray-500" />
        <Text type="secondary">Lọc theo tháng:</Text>
        <DatePicker
            picker="month"
            value={selectedDate}
            onChange={(date) => date && onChange(date)}
            format="MM/YYYY"
            allowClear={false}
            className="w-32"
        />
        <Text type="secondary" className="ml-auto text-xs w-full sm:w-auto mt-2 sm:mt-0">
            Hiển thị dữ liệu tháng {selectedDate.format('MM/YYYY')}
        </Text>
    </div>
);

const ProfilePage = () => {
    const { userId } = useParams();
    const navigate = useNavigate();
    const uid = userId ? parseInt(userId) : undefined;

    const [activeTab, setActiveTab] = useState('info');
    const [selectedDate, setSelectedDate] = useState<Dayjs>(() => dayjs());

    const [selectedViolation, setSelectedViolation] = useState<ViolationResponse | null>(null);
    const [selectedBonus, setSelectedBonus] = useState<BonusPointResponse | null>(null);
    const [selectedPermission, setSelectedPermission] = useState<PermissionRequestResponse | null>(null);
    const [loadingZalo, setLoadingZalo] = useState(false);
    const [loadingBotCode, setLoadingBotCode] = useState(false);
    const [botModalVisible, setBotModalVisible] = useState(false);
    const [botBindCode, setBotBindCode] = useState('');

    // Get user from cached users list
    const { data: users = [], isLoading: usersLoading } = useUsers();
    const user = useMemo(() => users.find(u => u.id === uid), [users, uid]);

    // Lazy load data - only fetch when tab is active
    const { data: violations = [], isLoading: violationsLoading } = useViolations({
        userId: uid,
        month: selectedDate.month() + 1,
        year: selectedDate.year(),
        enabled: activeTab === 'violations' && !!uid,
    });

    const { data: bonusPoints = [], isLoading: bonusLoading } = useBonusPoints({
        userId: uid,
        month: selectedDate.month() + 1,
        year: selectedDate.year(),
        enabled: activeTab === 'bonus' && !!uid,
    });

    const { data: permissionRequests = [], isLoading: permissionsLoading } = usePermissionRequests({
        userId: uid,
        month: selectedDate.month() + 1,
        year: selectedDate.year(),
        enabled: activeTab === 'permissions' && !!uid,
    });

    // Sort by created_at desc
    const sortedViolations = useMemo(() =>
        [...violations].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [violations]
    );
    const sortedBonusPoints = useMemo(() =>
        [...bonusPoints].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [bonusPoints]
    );
    const sortedPermissions = useMemo(() =>
        [...permissionRequests].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [permissionRequests]
    );

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

    const handleZaloLogin = async () => {
        try {
            setLoadingZalo(true);
            const data = await zaloService.getLoginUrl();
            if (data.data?.login_url && data.data?.code_verifier) {
                // Store code_verifier to local storage for the callback page to use
                localStorage.setItem('zalo_code_verifier', data.data.code_verifier);
                // Redirect to Zalo Auth window
                window.location.href = data.data.login_url;
            } else {
                message.error('Không thể tạo Link đăng nhập Zalo');
            }
        } catch (error: any) {
            message.error(error.message || 'Có lỗi xảy ra khi gọi Zalo API');
        } finally {
            setLoadingZalo(false);
        }
    };

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

    if (usersLoading) {
        return (
            <div className="p-4 md:p-8">
                <Card className="rounded-2xl shadow-sm border-gray-100">
                    <Skeleton active avatar paragraph={{ rows: 4 }} />
                </Card>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="p-4 md:p-8 flex flex-col items-center">
                <Text type="secondary">Không tìm thấy thông tin thành viên.</Text>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} className="mt-4">
                    Quay lại
                </Button>
            </div>
        );
    }

    return (
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-8 max-w-5xl mx-auto"
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
                                    <Title level={2} className="!m-0">{user.name}</Title>
                                    <Tag color="blue" className="mt-2 uppercase font-bold">{user.role_name}</Tag>
                                </div>
                                <Tag color={user.status === 'active' ? 'success' : 'error'} className="rounded-full px-4 sm:self-start">
                                    {user.status.toUpperCase()}
                                </Tag>
                            </div>
                        </div>
                    </div>

                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        className="mt-4"
                        items={[
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
                                                        <Text className="break-all">{user.email}</Text>
                                                    </div>
                                                    <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                        <PhoneOutlined className="text-indigo-500" />
                                                        <Text>{user.phone_number || 'Chưa cập nhật số điện thoại'}</Text>
                                                    </div>
                                                    <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                        <div className="flex items-center gap-3">
                                                            <Avatar src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/120px-Icon_of_Zalo.svg.png" size="small" />
                                                            <Text>Liên kết Zalo (Qua Ứng dụng)</Text>
                                                        </div>
                                                        {user.zalo_id ? (
                                                            <Tag color="green">Đã liên kết</Tag>
                                                        ) : (
                                                            <Button type="primary" size="small" className="bg-[#0068ff]" onClick={handleZaloLogin} loading={loadingZalo}>Liên kết</Button>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center justify-between bg-gray-50 p-3 rounded-xl border border-gray-50">
                                                        <div className="flex items-center gap-3">
                                                            <Avatar src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/120px-Icon_of_Zalo.svg.png" size="small" />
                                                            <Text>Liên kết Zalo (Chatbot <Tag color="green" className="ml-1 border-none shadow-sm rounded-md">Miễn phí</Tag>)</Text>
                                                        </div>
                                                        {(user as any).zalo_bot_id ? (
                                                            <Tag color="green">Đã liên kết</Tag>
                                                        ) : (
                                                            <Button type="primary" size="small" className="bg-[#0068ff]" onClick={handleGenerateBotCode} loading={loadingBotCode}>Lấy mã</Button>
                                                        )}
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
                                label: (
                                    <Space>
                                        <WarningOutlined />
                                        <span>Lỗi vi phạm</span>
                                        <Badge count={activeTab === 'violations' ? sortedViolations.length : 0} size="small" />
                                    </Space>
                                ),
                                children: (
                                    <>
                                        <FilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
                                        <Table
                                            dataSource={sortedViolations}
                                            columns={violationColumns}
                                            rowKey="id"
                                            loading={violationsLoading}
                                            pagination={{ pageSize: 10 }}
                                            scroll={{ x: 600 }}
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
                                label: (
                                    <Space>
                                        <TrophyOutlined />
                                        <span>Điểm cộng</span>
                                        <Badge count={activeTab === 'bonus' ? sortedBonusPoints.length : 0} size="small" />
                                    </Space>
                                ),
                                children: (
                                    <>
                                        <FilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
                                        <Table
                                            dataSource={sortedBonusPoints}
                                            columns={bonusColumns}
                                            rowKey="id"
                                            loading={bonusLoading}
                                            pagination={{ pageSize: 10 }}
                                            scroll={{ x: 600 }}
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
                                label: (
                                    <Space>
                                        <FileProtectOutlined />
                                        <span>Xin phép</span>
                                        <Badge count={activeTab === 'permissions' ? sortedPermissions.length : 0} size="small" />
                                    </Space>
                                ),
                                children: (
                                    <>
                                        <FilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
                                        <Table
                                            dataSource={sortedPermissions}
                                            columns={permissionColumns}
                                            rowKey="id"
                                            loading={permissionsLoading}
                                            pagination={{ pageSize: 10 }}
                                            scroll={{ x: 600 }}
                                            onRow={(record) => ({
                                                onClick: () => setSelectedPermission(record),
                                                className: 'cursor-pointer hover:bg-gray-50'
                                            })}
                                        />
                                    </>
                                )
                            }
                        ]}
                    />
                </Card>
            </motion.div>

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
            
            <Modal
                title={<><Avatar src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/120px-Icon_of_Zalo.svg.png" size="small" className="mr-2" /> Liên kết Zalo Bot (Miễn phí)</>}
                open={botModalVisible}
                onCancel={() => setBotModalVisible(false)}
                footer={null}
            >
                <div className="flex flex-col items-center p-4">
                    <Text className="mb-4 text-center">
                        Để nhận thông báo qua Zalo (miễn phí), vui lòng thực hiện các bước sau:
                    </Text>
                    <div className="w-full bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
                        <Text strong className="block mb-2">Bước 1:</Text>
                        <Text>Mở ứng dụng Zalo trên điện thoại, tìm kiếm <b>DUT AI Bot</b> (hoặc tên Bot bạn đã tạo).</Text>
                    </div>
                    <div className="w-full bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
                        <Text strong className="block mb-2">Bước 2:</Text>
                        <Text className="block mb-2">Gửi tin nhắn chính xác bằng đoạn mã sau cho Bot:</Text>
                        <div className="bg-white border-2 border-dashed border-[#0068ff] rounded-lg p-4 text-center">
                            <Text className="text-3xl font-bold tracking-[0.2em] text-[#0068ff]">
                                {botBindCode}
                            </Text>
                        </div>
                    </div>
                    <Text type="secondary" className="text-center italic mt-2">
                        Vui lòng làm mới trang (F5) sau khi bot báo liên kết thành công để cập nhật trạng thái.
                    </Text>
                </div>
            </Modal>
        </motion.div >
    );
};
export default ProfilePage;
