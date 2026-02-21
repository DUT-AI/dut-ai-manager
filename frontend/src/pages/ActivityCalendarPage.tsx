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
    Button,
    Modal
} from 'antd';
import {
    CalendarOutlined,
    WarningOutlined,
    PlusOutlined
} from '@ant-design/icons';
import { Grid } from 'antd';
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
import {
    MeetingModal,
    MeetingSection,
    ParticipantListModal
} from '@/components/meeting';
import { meetingService } from '@/services/api/meeting.service';
import useToggle from '@/hooks/useToggle';
import { useAuth } from '@/context/AuthContext';
import { BonusPointPermission, PermissionRequestPermission, ViolationPermission } from '@/types/rbac.types';

const { Title, Text } = Typography;

interface DailyDetailListProps {
    dailyData: DailySummaryResponse | null;
    onEditPermission: (item: PermissionRequestResponse) => void;
    onEditBonus: (item: BonusPointResponse) => void;
    onEditViolation: (item: ViolationResponse) => void;
    onViewParticipants: (meeting: any) => void;
    onEditMeeting: (meeting: any) => void;
    onDeleteMeeting: (id: number) => void;
    onRefresh: () => void;
}

const DailyDetailList = ({ dailyData, onEditPermission, onEditBonus, onEditViolation, onViewParticipants, onEditMeeting, onDeleteMeeting, onRefresh }: DailyDetailListProps) => (
    <div className="flex flex-col gap-8">
        <PermissionRequestSection
            data={dailyData?.permission_requests || []}
            onEdit={onEditPermission}
            onRefresh={onRefresh}
        />

        <Divider className="!m-0 border-gray-100" />

        <BonusPointSection
            data={dailyData?.bonus_points || []}
            onEdit={onEditBonus}
            onRefresh={onRefresh}
        />

        <Divider className="!m-0 border-gray-100" />

        <ViolationSection
            data={dailyData?.violations || []}
            onEdit={onEditViolation}
            onRefresh={onRefresh}
        />

        <Divider className="!m-0 border-gray-100" />

        <MeetingSection
            data={dailyData?.meetings || []}
            onViewParticipants={onViewParticipants}
            onEdit={onEditMeeting}
            onDelete={onDeleteMeeting}
        />
    </div>
);

interface GridMonthCalendarProps {
    selectedDate: Dayjs;
    activeDates: string[];
    onSelectDate: (date: Dayjs) => void;
    onNavigateMonth: (date: Dayjs) => void;
}

const GridMonthCalendar = ({ selectedDate, activeDates, onSelectDate, onNavigateMonth }: GridMonthCalendarProps) => {
    const daysInMonth = selectedDate.daysInMonth();
    const startOfMonth = selectedDate.startOf('month');
    const startDayOfWeek = startOfMonth.day();

    const days = [];
    for (let i = 0; i < startDayOfWeek; i++) {
        days.push(null);
    }
    for (let i = 0; i < daysInMonth; i++) {
        days.push(startOfMonth.add(i, 'day'));
    }

    const weekdayLabels = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between mb-4">
                <Button
                    type="text"
                    onClick={() => onNavigateMonth(selectedDate.subtract(1, 'month'))}
                    className="text-gray-400 hover:text-indigo-600 flex items-center p-0"
                >
                    <span className="text-lg">&larr;</span> <span className="ml-1">Trước</span>
                </Button>
                <div className="text-center">
                    <Text strong className="text-indigo-600 text-lg">Tháng {selectedDate.format('MM/YYYY')}</Text>
                </div>
                <Button
                    type="text"
                    onClick={() => onNavigateMonth(selectedDate.add(1, 'month'))}
                    className="text-gray-400 hover:text-indigo-600 flex items-center p-0"
                >
                    <span className="mr-1">Sau</span> <span className="text-lg">&rarr;</span>
                </Button>
            </div>

            <div className="grid grid-cols-7 gap-2">
                {weekdayLabels.map(label => (
                    <div key={label} className="text-center py-1 text-[10px] font-bold text-gray-400 uppercase">
                        {label}
                    </div>
                ))}
                {days.map((day, index) => {
                    if (!day) return <div key={`empty-${index}`} className="aspect-square" />;

                    const isSelected = day.isSame(selectedDate, 'day');
                    const isToday = day.isSame(dayjs(), 'day');
                    const hasActivity = activeDates.includes(day.format('YYYY-MM-DD'));

                    return (
                        <div
                            key={day.toString()}
                            role="button"
                            tabIndex={0}
                            onClick={() => onSelectDate(day)}
                            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelectDate(day); }}
                            className={`aspect-square flex flex-col items-center justify-center rounded-xl cursor-pointer transition-all border ${isSelected
                                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-md scale-110 z-10'
                                    : isToday
                                        ? 'bg-indigo-50 text-indigo-600 border-indigo-200 font-black'
                                        : 'bg-white text-gray-700 border-gray-50'
                                }`}
                        >
                            <span className="text-sm font-semibold">{day.format('D')}</span>
                            {hasActivity && (
                                <div className={`w-1 h-1 rounded-full mt-1 ${isSelected ? 'bg-white shadow-[0_0_4px_white]' : 'bg-indigo-500'}`} />
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const ActivityCalendarPage = () => {
    const { hasPermission } = useAuth();
    // State
    const [selectedDate, setSelectedDate] = useState<Dayjs>(() => dayjs());
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

    // Meeting States
    const [isMeetingModalOpen, setIsMeetingModalOpen] = useToggle(false);
    const [isParticipantModalOpen, setIsParticipantModalOpen] = useToggle(false);
    const [selectedMeeting, setSelectedMeeting] = useState<any | null>(null);
    const [editingMeeting, setEditingMeeting] = useState<any | null>(null);

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
        fetchDailyDetail(selectedDate);
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

    const handleMeetingSubmit = async (values: any) => {
        try {
            if (editingMeeting) {
                await meetingService.updateMeeting(editingMeeting.id, values);
                message.success('Đã cập nhật buổi sinh hoạt');
            } else {
                await meetingService.createMeeting(values);
                message.success('Đã tạo buổi sinh hoạt');
            }
            setIsMeetingModalOpen(false);
            setEditingMeeting(null);
            refreshData();
        } catch (error) {
            message.error(editingMeeting ? 'Cập nhật thất bại' : 'Tạo buổi sinh hoạt thất bại');
        }
    };

    const handleDeleteMeeting = (id: number) => {
        Modal.confirm({
            title: 'Xác nhận xóa',
            content: 'Bạn có chắc chắn muốn xóa buổi sinh hoạt này? Dữ liệu người tham gia cũng sẽ bị xóa.',
            okText: 'Xóa',
            okType: 'danger',
            cancelText: 'Hủy',
            onOk: async () => {
                try {
                    await meetingService.deleteMeeting(id);
                    message.success('Đã xóa buổi sinh hoạt');
                    refreshData();
                } catch (error) {
                    message.error('Xóa thất bại');
                }
            }
        });
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

    const openAddMeeting = () => {
        setEditingMeeting(null);
        setIsMeetingModalOpen(true);
    };

    const openEditMeeting = (meeting: any) => {
        setEditingMeeting(meeting);
        setIsMeetingModalOpen(true);
    };

    const openViewParticipants = (meeting: any) => {
        setSelectedMeeting(meeting);
        setIsParticipantModalOpen(true);
    };

    const screens = Grid.useBreakpoint();

    return (
        <div className="md:p-6 pb-20 md:pb-6 min-h-full">
            <Card
                className={`border-none ${screens.md ? 'shadow-md rounded-2xl' : 'shadow-none rounded-none'}`}
                styles={{ body: { padding: screens.md ? '24px' : '16px' } }}
            >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between mb-8 gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-gradient-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center text-white shadow-lg shrink-0">
                            <CalendarOutlined className="text-2xl md:text-3xl" />
                        </div>
                        <div>
                            <Title level={3} className="!m-0 text-xl md:text-2xl !leading-tight">Hoạt Động &amp; Điểm Danh</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Quản lý xin phép, điểm cộng và vi phạm cá nhân</Text>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 md:flex md:flex-row gap-2 w-full lg:w-auto">
                        {hasPermission(PermissionRequestPermission.CREATE) && (
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                className="bg-green-500 hover:bg-green-600 border-none rounded-xl h-10 font-semibold text-xs md:text-sm px-2 md:px-4"
                                onClick={openAddPermission}
                            >
                                Xin Phép
                            </Button>
                        )}
                        {hasPermission(BonusPointPermission.CREATE) && (
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                className="bg-indigo-500 hover:bg-indigo-600 border-none rounded-xl h-10 font-semibold text-xs md:text-sm px-2 md:px-4"
                                onClick={openAddBonus}
                            >
                                Điểm Cộng
                            </Button>
                        )}
                        {hasPermission(ViolationPermission.CREATE) && (
                            <Button
                                type="primary"
                                icon={<WarningOutlined />}
                                className="bg-red-500 hover:bg-red-600 border-none rounded-xl h-10 font-semibold text-xs md:text-sm px-2 md:px-4"
                                onClick={openAddViolation}
                            >
                                Vi Phạm
                            </Button>
                        )}
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            className="bg-blue-600 hover:bg-blue-700 border-none rounded-xl h-10 font-semibold text-xs md:text-sm px-2 md:px-4 col-span-2 md:col-auto"
                            onClick={openAddMeeting}
                        >
                            Tạo Meeting
                        </Button>
                    </div>
                </div>

                <div className={`${screens.md ? 'bg-gray-50/50 p-6 border border-gray-100' : 'bg-transparent p-0 border-none'} rounded-2xl`}>
                    {!screens.md ? (
                        <GridMonthCalendar
                            selectedDate={selectedDate}
                            activeDates={activeDates}
                            onSelectDate={(day) => {
                                setSelectedDate(day);
                                fetchDailyDetail(day);
                                setDrawerVisible(true);
                            }}
                            onNavigateMonth={setSelectedDate}
                        />
                    ) : (
                        <Calendar
                            onSelect={onSelect}
                            cellRender={dateCellRender}
                            fullscreen={true}
                            className="custom-calendar rounded-xl overflow-hidden"
                        />
                    )}
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
                width={screens.md ? 450 : '100%'}
                className="activity-drawer"
            >
                {loading ? (
                    <div className="h-full flex items-center justify-center">
                        <Spin size="large" tip="Đang tải dữ liệu..." />
                    </div>
                ) : (
                    <DailyDetailList
                        dailyData={dailyData}
                        onEditPermission={openEditPermission}
                        onEditBonus={openEditBonus}
                        onEditViolation={openEditViolation}
                        onViewParticipants={openViewParticipants}
                        onEditMeeting={openEditMeeting}
                        onDeleteMeeting={handleDeleteMeeting}
                        onRefresh={refreshData}
                    />
                )}
            </Drawer>

            {/* Modals */}
            <MeetingModal
                open={isMeetingModalOpen}
                editingItem={editingMeeting}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleMeetingSubmit}
                onCancel={() => {
                    setIsMeetingModalOpen(false);
                    setEditingMeeting(null);
                }}
            />

            <ParticipantListModal
                open={isParticipantModalOpen}
                meeting={selectedMeeting}
                onCancel={() => setIsParticipantModalOpen(false)}
            />
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
