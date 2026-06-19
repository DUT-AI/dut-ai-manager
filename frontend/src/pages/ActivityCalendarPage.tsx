import { useState, useEffect, useReducer, useMemo } from 'react';
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
    Modal,
    Space
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
import { homeworkService } from '@/services/api/homework.service';
import type { DailySummaryResponse, PermissionRequestResponse, BonusPointResponse, ViolationResponse } from '@/types/activity.types';
import type { Homework } from '@/types/homework.types';
import type { MeetingResponse } from '@/types/meeting.types';
import type { UserResponse } from '@/types/user.types';
import { violationService } from '@/services/api/violation.service';
import { activityService } from '@/services/api/activity.service';
import { useMonthlyActivities, useDailyActivitySummary } from '@/hooks/useActivities';
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
import { useCapacity } from '@/context/CapacityContext';
import { CapacityWarning } from '@/components/CapacityWarning';
import { Agentation } from 'agentation';
import { BonusPointPermission, PermissionRequestPermission, ViolationPermission } from '@/types/rbac.types';
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

// --- Modal state management via useReducer ---
type ActivityModalState = {
    isPermissionModalOpen: boolean;
    isBonusModalOpen: boolean;
    isViolationModalOpen: boolean;
    editingPermission: PermissionRequestResponse | null;
    editingBonus: BonusPointResponse | null;
    editingViolation: ViolationResponse | null;
    isMeetingModalOpen: boolean;
    isParticipantModalOpen: boolean;
    selectedMeeting: any | null;
    editingMeeting: any | null;
};

type ActivityModalAction =
    | { type: 'OPEN_PERMISSION'; payload?: PermissionRequestResponse }
    | { type: 'CLOSE_PERMISSION' }
    | { type: 'OPEN_BONUS'; payload?: BonusPointResponse }
    | { type: 'CLOSE_BONUS' }
    | { type: 'OPEN_VIOLATION'; payload?: ViolationResponse }
    | { type: 'CLOSE_VIOLATION' }
    | { type: 'OPEN_MEETING'; payload?: any }
    | { type: 'CLOSE_MEETING' }
    | { type: 'OPEN_PARTICIPANTS'; payload: any }
    | { type: 'CLOSE_PARTICIPANTS' };

const activityModalInitialState: ActivityModalState = {
    isPermissionModalOpen: false,
    isBonusModalOpen: false,
    isViolationModalOpen: false,
    editingPermission: null,
    editingBonus: null,
    editingViolation: null,
    isMeetingModalOpen: false,
    isParticipantModalOpen: false,
    selectedMeeting: null,
    editingMeeting: null,
};

function activityModalReducer(state: ActivityModalState, action: ActivityModalAction): ActivityModalState {
    switch (action.type) {
        case 'OPEN_PERMISSION':
            return { ...state, isPermissionModalOpen: true, editingPermission: action.payload ?? null };
        case 'CLOSE_PERMISSION':
            return { ...state, isPermissionModalOpen: false, editingPermission: null };
        case 'OPEN_BONUS':
            return { ...state, isBonusModalOpen: true, editingBonus: action.payload ?? null };
        case 'CLOSE_BONUS':
            return { ...state, isBonusModalOpen: false, editingBonus: null };
        case 'OPEN_VIOLATION':
            return { ...state, isViolationModalOpen: true, editingViolation: action.payload ?? null };
        case 'CLOSE_VIOLATION':
            return { ...state, isViolationModalOpen: false, editingViolation: null };
        case 'OPEN_MEETING':
            return { ...state, isMeetingModalOpen: true, editingMeeting: action.payload ?? null };
        case 'CLOSE_MEETING':
            return { ...state, isMeetingModalOpen: false, editingMeeting: null };
        case 'OPEN_PARTICIPANTS':
            return { ...state, isParticipantModalOpen: true, selectedMeeting: action.payload };
        case 'CLOSE_PARTICIPANTS':
            return { ...state, isParticipantModalOpen: false };
        default:
            return state;
    }
}

const ActivityCalendarPage = () => {
    const { hasPermission } = useAuth();
    const { capacityStatus } = useCapacity();
    const isOverload = capacityStatus === 'overload';

    // State
    const [selectedDate, setSelectedDate] = useState<Dayjs>(() => dayjs());
    const [drawerVisible, setDrawerVisible] = useToggle(false);

    // React Query Hooks
    const { data: activeDates = [] } = useMonthlyActivities(selectedDate.month() + 1, selectedDate.year());
    const { data: dailyData, isLoading: loading, refetch: refreshData } = useDailyActivitySummary(selectedDate.format('YYYY-MM-DD'));

    const [users, setUsers] = useState<UserResponse[]>([]);
    const [homeworks, setHomeworks] = useState<Homework[]>([]);
    const [allMeetings, setAllMeetings] = useState<MeetingResponse[]>([]);

    // Modal state via useReducer
    const [modalState, dispatch] = useReducer(activityModalReducer, activityModalInitialState);
    const {
        isPermissionModalOpen, isBonusModalOpen, isViolationModalOpen,
        editingPermission, editingBonus, editingViolation,
        isMeetingModalOpen, isParticipantModalOpen, selectedMeeting, editingMeeting,
    } = modalState;

    // Lấy dữ liệu mới nhất của meeting đang được chọn
    const currentMeeting = useMemo(() => {
        if (!selectedMeeting) return null;
        const latest = dailyData?.meetings.find(m => m.id === selectedMeeting.id);
        return latest || selectedMeeting;
    }, [dailyData, selectedMeeting]);

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

    const fetchAllHomeworks = async () => {
        try {
            const data = await homeworkService.getAll();
            setHomeworks(data || []);
        } catch (error) {
            console.error('Failed to fetch homeworks', error);
        }
    };

    const fetchAllMeetings = async () => {
        try {
            const res = await meetingService.getMeetings();
            if (res.is_success) {
                setAllMeetings(res.data || []);
            }
        } catch (error) {
            console.error('Failed to fetch meetings', error);
        }
    };

    useEffect(() => {
        fetchAllUsers();
        fetchAllHomeworks();
        fetchAllMeetings();
    }, []);

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
            dispatch({ type: 'CLOSE_PERMISSION' });
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
            dispatch({ type: 'CLOSE_BONUS' });
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
            dispatch({ type: 'CLOSE_VIOLATION' });
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
            dispatch({ type: 'CLOSE_MEETING' });
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
    const openAddPermission = () => dispatch({ type: 'OPEN_PERMISSION' });
    const openAddBonus = () => dispatch({ type: 'OPEN_BONUS' });
    const openAddViolation = () => dispatch({ type: 'OPEN_VIOLATION' });

    const openEditPermission = (item: PermissionRequestResponse) => dispatch({ type: 'OPEN_PERMISSION', payload: item });
    const openEditBonus = (item: BonusPointResponse) => dispatch({ type: 'OPEN_BONUS', payload: item });
    const openEditViolation = (item: ViolationResponse) => dispatch({ type: 'OPEN_VIOLATION', payload: item });
    const openAddMeeting = () => dispatch({ type: 'OPEN_MEETING' });
    const openEditMeeting = (meeting: any) => dispatch({ type: 'OPEN_MEETING', payload: meeting });
    const openViewParticipants = (meeting: any) => dispatch({ type: 'OPEN_PARTICIPANTS', payload: meeting });

    const screens = Grid.useBreakpoint();

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="md:p-6 pb-20 md:pb-6 min-h-full"
        >
            <CapacityWarning />
            <Card
                className={`border-none ${screens.md ? 'shadow-md rounded-2xl' : 'shadow-none rounded-none'}`}
                styles={{ body: { padding: screens.md ? '24px' : '16px' } }}
            >
                <motion.div variants={itemVariants} className="flex flex-col lg:flex-row lg:items-center justify-between mb-8 gap-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-600 shadow-sm">
                            <CalendarOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-indigo-600">Hoạt động & Điểm danh</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Quản lý xin phép, điểm cộng và vi phạm cá nhân</Text>
                        </div>
                    </Space>

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
                            className={`border-none rounded-xl h-10 font-semibold text-xs md:text-sm px-2 md:px-4 col-span-2 md:col-auto ${isOverload ? 'bg-gray-400 text-gray-200 opacity-70 cursor-not-allowed hover:bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
                            onClick={openAddMeeting}
                            disabled={isOverload}
                            title={isOverload ? 'Phòng lab đang quá tải, không thể tạo lịch mới' : undefined}
                        >
                            Tạo Meeting
                        </Button>
                    </div>
                </motion.div>

                <motion.div variants={itemVariants} className={`${screens.md ? 'bg-gray-50/50 p-6 border border-gray-100' : 'bg-transparent p-0 border-none'} rounded-2xl`}>
                    {!screens.md ? (
                        <GridMonthCalendar
                            selectedDate={selectedDate}
                            activeDates={activeDates}
                            onSelectDate={(day) => {
                                setSelectedDate(day);
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
                </motion.div>
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
                key={editingMeeting?.id ?? 'meeting-create'}
                open={isMeetingModalOpen}
                editingItem={editingMeeting}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleMeetingSubmit}
                onCancel={() => dispatch({ type: 'CLOSE_MEETING' })}
            />

            <ParticipantListModal
                key={currentMeeting?.id ?? 'participants'}
                open={isParticipantModalOpen}
                meeting={currentMeeting}
                onCancel={() => dispatch({ type: 'CLOSE_PARTICIPANTS' })}
            />
            <PermissionRequestModal
                key={editingPermission?.id ?? 'perm-create'}
                open={isPermissionModalOpen}
                editingItem={editingPermission}
                initialDate={getInitialDate()}
                homeworks={homeworks}
                meetings={allMeetings}
                onSubmit={handlePermissionSubmit}
                onCancel={() => dispatch({ type: 'CLOSE_PERMISSION' })}
            />

            <BonusPointModal
                key={editingBonus?.id ?? 'bonus-create'}
                open={isBonusModalOpen}
                editingItem={editingBonus}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleBonusSubmit}
                onCancel={() => dispatch({ type: 'CLOSE_BONUS' })}
            />

            <ViolationModal
                key={editingViolation?.id ?? 'violation-create'}
                open={isViolationModalOpen}
                editingItem={editingViolation}
                initialDate={getInitialDate()}
                users={users}
                onSubmit={handleViolationSubmit}
                onCancel={() => dispatch({ type: 'CLOSE_VIOLATION' })}
            />

            <Agentation />

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
        </motion.div>
    );
};

export default ActivityCalendarPage;
