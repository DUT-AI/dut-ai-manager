import { useState, useEffect } from 'react';
import {
    Calendar,
    Badge,
    Card,
    Drawer,
    Typography,
    Divider,
    Spin,
    message,
    Button
} from 'antd';
import {
    CalendarOutlined,
    WarningOutlined,
    FileTextOutlined,
    PlusOutlined
} from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { permissionService } from '@/services/api/permission.service';
import { bonusPointService } from '@/services/api/bonus-point.service';
import { userService } from '@/services/api/user.service';
import type { DailySummaryResponse, PermissionRequestResponse, BonusPointResponse, ViolationResponse } from '@/types/activity.types';
import type { UserResponse } from '@/types/user.types';
import { violationService } from '@/services/api/violation.service';
import { activityService } from '@/services/api/activity.service';
import {
    PermissionRequestSection,
    BonusPointSection,
    ViolationSection,
    PermissionRequestModal,
    BonusPointModal,
    ViolationModal
} from '@/components/activity';
import useToggle from '@/hooks/useToggle';

const { Title, Text } = Typography;

const ActivityCalendarPage = () => {
    // State
    const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
    const [drawerVisible, setDrawerVisible] = useToggle(false);
    const [dailyData, setDailyData] = useState<DailySummaryResponse | null>(null);
    const [loading, setLoading] = useToggle(false);
    const [activeDates, setActiveDates] = useState<string[]>([]);
    const [users, setUsers] = useState<UserResponse[]>([]);

    // Modals State
    const [isPermissionModalOpen, setIsPermissionModalOpen] = useToggle(false);
    const [isBonusModalOpen, setIsBonusModalOpen] = useToggle(false);
    const [isViolationModalOpen, setIsViolationModalOpen] = useToggle(false);
    const [editingPermission, setEditingPermission] = useState<PermissionRequestResponse | null>(null);
    const [editingBonus, setEditingBonus] = useState<BonusPointResponse | null>(null);
    const [editingViolation, setEditingViolation] = useState<ViolationResponse | null>(null);

    // Fetch Data
    const fetchMonthlyData = async (date: Dayjs) => {
        try {
            const res = await activityService.getMonthlyStats(date.month() + 1, date.year());
            if (res.is_success) {
                setActiveDates(res.data || []);
            }
        } catch (error) {
            console.error('Failed to fetch monthly stats', error);
        }
    };

    const fetchDailyDetail = async (date: Dayjs) => {
        setLoading(true);
        try {
            const dateStr = date.format('YYYY-MM-DD');
            const res = await activityService.getDailySummary(dateStr);
            if (res.is_success) {
                setDailyData(res.data || null);
            } else {
                message.error(res.message || 'Failed to fetch details');
            }
        } catch (error) {
            message.error('Connection error');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllUsers = async () => {
        try {
            const res = await userService.getUsers();
            if (res.is_success) {
                setUsers(res.data || []);
            }
        } catch (error) {
            message.error('Connection error while fetching users');
        }
    };

    const refreshData = () => {
        fetchDailyDetail(selectedDate);
        fetchMonthlyData(selectedDate);
    };

    useEffect(() => {
        fetchMonthlyData(selectedDate);
        fetchAllUsers();
    }, [selectedDate.month(), selectedDate.year()]);

    const dateCellRender = (value: Dayjs) => {
        const dateStr = value.format('YYYY-MM-DD');
        const hasActivity = activeDates.includes(dateStr);
        if (hasActivity) {
            return (
                <div className="flex justify-center mt-1">
                    <Badge status="processing" color="#667eea" />
                </div>
            );
        }
        return null;
    };

    const onSelect = (newValue: Dayjs) => {
        setSelectedDate(newValue);
        fetchDailyDetail(newValue);
        setDrawerVisible(true);
    };

    const getInitialDate = () => {
        return selectedDate.isSame(dayjs(), 'day')
            ? dayjs()
            : selectedDate.hour(dayjs().hour()).minute(dayjs().minute());
    };

    // --- CRUD Handlers ---

    const handlePermissionSubmit = async (values: any) => {
        try {
            if (editingPermission) {
                await permissionService.updatePermission(editingPermission.id, values);
                message.success('Đã cập nhật đơn xin phép');
            } else {
                await permissionService.createPermission(values);
                message.success('Đã tạo đơn xin phép');
            }
            setIsPermissionModalOpen(false);
            setEditingPermission(null);
            refreshData();
        } catch (error) {
            message.error('Thao tác thất bại');
        }
    };

    const handleBonusSubmit = async (values: any) => {
        try {
            if (editingBonus) {
                await bonusPointService.updateBonusPoint(editingBonus.id, values);
                message.success('Đã cập nhật điểm cộng');
            } else {
                await bonusPointService.createBonusPoint(values);
                message.success('Đã thêm điểm cộng');
            }
            setIsBonusModalOpen(false);
            setEditingBonus(null);
            refreshData();
        } catch (error) {
            message.error('Thao tác thất bại');
        }
    };

    const handleViolationSubmit = async (values: any) => {
        try {
            if (editingViolation) {
                await violationService.updateViolation(editingViolation.id, values);
                message.success('Đã cập nhật vi phạm');
            } else {
                await violationService.createViolation(values);
                message.success('Đã ghi nhận vi phạm');
            }
            setIsViolationModalOpen(false);
            setEditingViolation(null);
            refreshData();
        } catch (error) {
            message.error('Thao tác thất bại');
        }
    };

    // Open Modals
    const openAddPermission = () => {
        setEditingPermission(null);
        setIsPermissionModalOpen(true);
    };

    const openAddBonus = () => {
        setEditingBonus(null);
        setIsBonusModalOpen(true);
    };

    const openAddViolation = () => {
        setEditingViolation(null);
        setIsViolationModalOpen(true);
    };

    const openEditPermission = (item: PermissionRequestResponse) => {
        setEditingPermission(item);
        setIsPermissionModalOpen(true);
    };

    const openEditBonus = (item: BonusPointResponse) => {
        setEditingBonus(item);
        setIsBonusModalOpen(true);
    };

    const openEditViolation = (item: ViolationResponse) => {
        setEditingViolation(item);
        setIsViolationModalOpen(true);
    };

    return (
        <div className="p-6">
            <Card className="shadow-md border-none rounded-2xl overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-linear-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center text-white shadow-lg">
                            <CalendarOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="!m-0">Hoạt Động &amp; Chấm Công</Title>
                            <Text type="secondary">Quản lý xin phép, điểm cộng và vi phạm cá nhân</Text>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            className="bg-green-500 hover:bg-green-600 border-none"
                            onClick={openAddBonus}
                        >
                            Thêm Điểm Cộng
                        </Button>
                        <Button
                            type="primary"
                            icon={<WarningOutlined />}
                            className="bg-red-500 hover:bg-red-600 border-none"
                            onClick={openAddViolation}
                        >
                            Thêm Vi Phạm
                        </Button>
                        <Button
                            icon={<FileTextOutlined />}
                            onClick={openAddPermission}
                        >
                            Xin Phép
                        </Button>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-gray-100">
                    <Calendar
                        onSelect={onSelect}
                        cellRender={dateCellRender}
                        fullscreen={true}
                        className="custom-calendar"
                    />
                </div>
            </Card>

            <Drawer
                title={
                    <div className="flex flex-col">
                        <Text strong className="text-lg">Chi tiết ngày {selectedDate.format('DD/MM/YYYY')}</Text>
                        <Text type="secondary" className="text-xs">Danh sách các hoạt động đã ghi nhận</Text>
                    </div>
                }
                placement="right"
                onClose={() => setDrawerVisible(false)}
                open={drawerVisible}
                width={450}
                className="activity-drawer"
            >
                {loading ? (
                    <div className="h-full flex items-center justify-center">
                        <Spin size="large" tip="Đang tải dữ liệu..." />
                    </div>
                ) : (
                    <div className="flex flex-col gap-8 pb-10">
                        <PermissionRequestSection
                            data={dailyData?.permission_requests || []}
                            onEdit={openEditPermission}
                            onRefresh={refreshData}
                        />

                        <Divider className="!m-0" />

                        <BonusPointSection
                            data={dailyData?.bonus_points || []}
                            onEdit={openEditBonus}
                            onRefresh={refreshData}
                        />

                        <Divider className="!m-0" />

                        <ViolationSection
                            data={dailyData?.violations || []}
                            onEdit={openEditViolation}
                            onRefresh={refreshData}
                        />
                    </div>
                )}
            </Drawer>

            {/* Modals */}
            <PermissionRequestModal
                open={isPermissionModalOpen}
                editingItem={editingPermission}
                initialDate={getInitialDate()}
                onSubmit={handlePermissionSubmit}
                onCancel={() => setIsPermissionModalOpen(false)}
            />

            <BonusPointModal
                open={isBonusModalOpen}
                editingItem={editingBonus}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleBonusSubmit}
                onCancel={() => setIsBonusModalOpen(false)}
            />

            <ViolationModal
                open={isViolationModalOpen}
                editingItem={editingViolation}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleViolationSubmit}
                onCancel={() => setIsViolationModalOpen(false)}
            />

            <style>{`
                .custom-calendar .ant-picker-calendar-header {
                    padding-bottom: 20px;
                }
                .custom-calendar .ant-picker-cell-selected .ant-picker-calendar-date {
                    background: rgba(102, 126, 234, 0.1) !important;
                    border-top: 2px solid #667eea !important;
                }
                .activity-drawer .ant-drawer-header {
                    background: #f8fafc;
                    border-bottom: 1px solid #f1f5f9;
                }
            `}</style>
        </div>
    );
};

export default ActivityCalendarPage;
