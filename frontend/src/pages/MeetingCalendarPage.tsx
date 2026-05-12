import { useState, useMemo, useCallback, useReducer } from 'react';
import { Button, Typography, Tooltip, Spin, message } from 'antd';
import {
    LeftOutlined,
    RightOutlined,
    PlusOutlined,
    CalendarOutlined,
    ClockCircleOutlined,
    SafetyCertificateOutlined,
    UserOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import type { MeetingResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';
import { useMeetingsByWeek, useCreateMeeting, useUpdateMeeting, useDeleteMeeting } from '@/hooks/useMeetings';
import { MeetingDetailDrawer } from '@/components/meeting/MeetingDetailDrawer';
import { MeetingModal } from '@/components/meeting/MeetingModal';
import { useUsers } from '@/hooks/useUsers';
import { motion, type Variants } from 'motion/react';

dayjs.extend(isoWeek);

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.3, ease: "easeOut" }
    }
};

// Timeline configuration
const HOUR_START = 0;
const HOUR_END = 24;
const HOUR_HEIGHT = 60; // pixels per hour
const TOTAL_HOURS = HOUR_END - HOUR_START;

const DAY_LABELS = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN'];

// Color palette for meetings
const MEETING_COLORS = [
    { bg: 'rgba(99, 102, 241, 0.15)', border: '#6366f1', text: '#4338ca' },
    { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', text: '#059669' },
    { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#d97706' },
    { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#dc2626' },
    { bg: 'rgba(139, 92, 246, 0.15)', border: '#8b5cf6', text: '#7c3aed' },
    { bg: 'rgba(236, 72, 153, 0.15)', border: '#ec4899', text: '#db2777' },
    { bg: 'rgba(14, 165, 233, 0.15)', border: '#0ea5e9', text: '#0284c7' },
    { bg: 'rgba(168, 85, 247, 0.15)', border: '#a855f7', text: '#9333ea' },
];

interface PositionedMeeting {
    meeting: MeetingResponse;
    top: number;
    height: number;
    left: number; // percentage
    width: number; // percentage
    color: (typeof MEETING_COLORS)[number];
}

// --- Modal state management via useReducer ---
type MeetingModalState = {
    selectedMeeting: MeetingResponse | null;
    drawerOpen: boolean;
    modalOpen: boolean;
    editingMeeting: MeetingResponse | null;
};

type MeetingModalAction =
    | { type: 'OPEN_DRAWER'; payload: MeetingResponse }
    | { type: 'CLOSE_DRAWER' }
    | { type: 'OPEN_MODAL'; payload?: { meeting?: MeetingResponse } }
    | { type: 'CLOSE_MODAL' };

const meetingModalInitialState: MeetingModalState = {
    selectedMeeting: null,
    drawerOpen: false,
    modalOpen: false,
    editingMeeting: null,
};

function meetingModalReducer(state: MeetingModalState, action: MeetingModalAction): MeetingModalState {
    switch (action.type) {
        case 'OPEN_DRAWER':
            return { ...state, drawerOpen: true, selectedMeeting: action.payload };
        case 'CLOSE_DRAWER':
            return { ...state, drawerOpen: false };
        case 'OPEN_MODAL':
            return { ...state, modalOpen: true, editingMeeting: action.payload?.meeting ?? null };
        case 'CLOSE_MODAL':
            return { ...state, modalOpen: false, editingMeeting: null };
        default:
            return state;
    }
}

const MeetingCalendarPage = () => {
    const [currentWeekStart, setCurrentWeekStart] = useState<Dayjs>(() =>
        dayjs().startOf('isoWeek')
    );
    const [modalInitialDate, setModalInitialDate] = useState<Dayjs>(() => dayjs());
    const [modalState, dispatch] = useReducer(meetingModalReducer, meetingModalInitialState);
    const { selectedMeeting, drawerOpen, modalOpen, editingMeeting } = modalState;



    const weekEnd = currentWeekStart.add(6, 'day');
    const startDateStr = currentWeekStart.format('YYYY-MM-DD');
    const endDateStr = weekEnd.format('YYYY-MM-DD');

    const { data: meetings = [], isLoading } = useMeetingsByWeek(startDateStr, endDateStr);
    const { data: usersData } = useUsers();
    const users = useMemo(() => (usersData as any)?.data ?? usersData ?? [], [usersData]);

    // Lấy dữ liệu mới nhất của meeting đang được chọn từ cache của React Query
    const currentMeeting = useMemo(() => {
        if (!selectedMeeting) return null;
        // Tìm trong list meetings vừa được refetch
        const latest = meetings.find(m => m.id === selectedMeeting.id);
        return latest || selectedMeeting;
    }, [meetings, selectedMeeting]);

    const createMutation = useCreateMeeting();
    const updateMutation = useUpdateMeeting();
    const deleteMutation = useDeleteMeeting();

    // Navigation
    const goToPrevWeek = () => setCurrentWeekStart(prev => prev.subtract(1, 'week'));
    const goToNextWeek = () => setCurrentWeekStart(prev => prev.add(1, 'week'));
    const goToToday = () => setCurrentWeekStart(dayjs().startOf('isoWeek'));

    // Week days
    const weekDays = useMemo(() => {
        return Array.from({ length: 7 }, (_, i) => currentWeekStart.add(i, 'day'));
    }, [currentWeekStart]);

    // Group meetings by day of week (ISO: 1=Monday)
    const meetingsByDay = useMemo(() => {
        const grouped: Record<number, MeetingResponse[]> = {};
        for (let i = 1; i <= 7; i++) grouped[i] = [];

        meetings.forEach(m => {
            const day = dayjs(m.start_time).isoWeekday();
            if (grouped[day]) grouped[day].push(m);
        });

        return grouped;
    }, [meetings]);

    // Calculate positioned meetings for a given day - handle overlaps
    const getPositionedMeetings = useCallback(
        (dayMeetings: MeetingResponse[]): PositionedMeeting[] => {
            if (dayMeetings.length === 0) return [];

            // Sort by start time
            const sorted = [...dayMeetings].sort(
                (a, b) => dayjs(a.start_time).valueOf() - dayjs(b.start_time).valueOf()
            );

            // Find overlapping groups
            const groups: MeetingResponse[][] = [];
            let currentGroup: MeetingResponse[] = [sorted[0]];
            let groupEnd = dayjs(sorted[0].end_time);

            for (let i = 1; i < sorted.length; i++) {
                const meetingStart = dayjs(sorted[i].start_time);
                if (meetingStart.isBefore(groupEnd)) {
                    // Overlapping
                    currentGroup.push(sorted[i]);
                    const thisEnd = dayjs(sorted[i].end_time);
                    if (thisEnd.isAfter(groupEnd)) groupEnd = thisEnd;
                } else {
                    groups.push(currentGroup);
                    currentGroup = [sorted[i]];
                    groupEnd = dayjs(sorted[i].end_time);
                }
            }
            groups.push(currentGroup);

            // Position each meeting
            const positioned: PositionedMeeting[] = [];
            let colorIdx = 0;

            groups.forEach(group => {
                const count = group.length;
                group.forEach((meeting, index) => {
                    const startH = dayjs(meeting.start_time).hour() + dayjs(meeting.start_time).minute() / 60;
                    const endH = dayjs(meeting.end_time).hour() + dayjs(meeting.end_time).minute() / 60;
                    const clampedStart = Math.max(startH, HOUR_START);
                    const clampedEnd = Math.min(endH, HOUR_END);
                    const top = (clampedStart - HOUR_START) * HOUR_HEIGHT;
                    const height = Math.max((clampedEnd - clampedStart) * HOUR_HEIGHT, 28);

                    positioned.push({
                        meeting,
                        top,
                        height,
                        left: (index / count) * 100,
                        width: 100 / count,
                        color: MEETING_COLORS[colorIdx % MEETING_COLORS.length],
                    });
                    colorIdx++;
                });
            });

            return positioned;
        },
        []
    );

    // Handle meeting click
    const handleMeetingClick = (meeting: MeetingResponse) => {
        dispatch({ type: 'OPEN_DRAWER', payload: meeting });
    };

    // Handle create
    const handleCreate = (dayDate: Dayjs) => {
        setModalInitialDate(dayDate);
        dispatch({ type: 'OPEN_MODAL' });
    };

    // Handle edit from drawer
    const handleEdit = (meeting: MeetingResponse) => {
        dispatch({ type: 'CLOSE_DRAWER' });
        setModalInitialDate(dayjs(meeting.start_time));
        dispatch({ type: 'OPEN_MODAL', payload: { meeting } });
    };

    // Handle delete
    const handleDelete = (id: number) => {
        deleteMutation.mutate(id, {
            onSuccess: () => {
                message.success('Đã xóa buổi sinh hoạt');
                dispatch({ type: 'CLOSE_DRAWER' });
            },
            onError: () => message.error('Không thể xóa'),
        });
    };

    // Handle submit (create or edit)
    const handleSubmit = (values: any) => {
        if (editingMeeting) {
            updateMutation.mutate(
                { id: editingMeeting.id, data: values },
                {
                    onSuccess: () => {
                        message.success('Đã cập nhật');
                        dispatch({ type: 'CLOSE_MODAL' });
                    },
                    onError: () => message.error('Không thể cập nhật'),
                }
            );
        } else {
            createMutation.mutate(values, {
                onSuccess: () => {
                    message.success('Đã tạo buổi sinh hoạt');
                    dispatch({ type: 'CLOSE_MODAL' });
                },
                onError: () => message.error('Không thể tạo'),
            });
        }
    };

    // Check if a day is today
    const isToday = (day: Dayjs) => day.isSame(dayjs(), 'day');

    // Current time indicator position
    const now = dayjs();
    const nowHour = now.hour() + now.minute() / 60;
    const showNowLine = nowHour >= HOUR_START && nowHour <= HOUR_END;
    const nowLineTop = (nowHour - HOUR_START) * HOUR_HEIGHT;

    // Is current week
    const isCurrentWeek = currentWeekStart.isSame(dayjs().startOf('isoWeek'), 'day');

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="min-w-full bg-white"
            style={{ minWidth: 1460 }}
        >
            {/* Header */}
            <motion.div variants={itemVariants} className="px-6 py-4 border-b border-gray-100 bg-white sticky top-0 z-20">
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <div className="flex items-center gap-3">
                        <CalendarOutlined className="text-2xl text-indigo-500" />
                        <div>
                            <Title level={4} className="!mb-0 !text-gray-800">
                                Lịch Meeting
                            </Title>
                            <Text type="secondary" className="text-xs">
                                Tuần {currentWeekStart.isoWeek()} •{' '}
                                {currentWeekStart.format('DD/MM')} – {weekEnd.format('DD/MM/YYYY')}
                            </Text>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <Button.Group>
                            <Button icon={<LeftOutlined />} onClick={goToPrevWeek} />
                            <Button onClick={goToToday} type={isCurrentWeek ? 'primary' : 'default'}>
                                Hôm nay
                            </Button>
                            <Button icon={<RightOutlined />} onClick={goToNextWeek} />
                        </Button.Group>
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleCreate(dayjs())}>
                            Tạo mới
                        </Button>
                    </div>
                </div>
            </motion.div>

            {/* Calendar grid */}
            {isLoading ? (
                <div className="flex-1 flex items-center justify-center p-20">
                    <Spin size="large" />
                </div>
            ) : (
                <motion.div variants={itemVariants}>
                    <div className="flex" style={{ minWidth: 1460 }}>
                        {/* Time gutter */}
                        <div className="w-16 flex-shrink-0 border-r border-gray-100 bg-gray-50/50">
                            {/* Day header spacer */}
                            <div className="h-16 border-b border-gray-100" />
                            {/* Hour labels */}
                            <div className="relative" style={{ height: TOTAL_HOURS * HOUR_HEIGHT }}>
                                {Array.from({ length: TOTAL_HOURS + 1 }, (_, i) => (
                                    <div
                                        key={HOUR_START + i}
                                        className="absolute w-full text-right pr-2 text-[11px] text-gray-400 font-medium"
                                        style={{ top: i * HOUR_HEIGHT - 7 }}
                                    >
                                        {`${HOUR_START + i}:00`}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Day columns */}
                        {weekDays.map((day, dayIdx) => {
                            const dayNum = day.isoWeekday();
                            const dayMeetings = meetingsByDay[dayNum] || [];
                            const positioned = getPositionedMeetings(dayMeetings);
                            const today = isToday(day);

                            return (
                                <div
                                    key={dayIdx}
                                    className={`flex-1 border-r border-gray-100 last:border-r-0 ${today ? 'bg-indigo-50/30' : ''
                                        }`}
                                    style={{ minWidth: 200 }}
                                >
                                    {/* Day header */}
                                    <div
                                        role="button"
                                        tabIndex={0}
                                        className={`h-16 flex flex-col items-center justify-center border-b border-gray-100 cursor-pointer transition-colors hover:bg-gray-50 ${today ? 'bg-indigo-50' : ''
                                            }`}
                                        onClick={() => handleCreate(day)}
                                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleCreate(day); }}
                                    >
                                        <Text
                                            className={`text-xs font-semibold uppercase tracking-wide ${today ? '!text-indigo-600' : '!text-gray-500'
                                                }`}
                                        >
                                            {DAY_LABELS[dayIdx]}
                                        </Text>
                                        <div
                                            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mt-0.5 ${today
                                                ? 'bg-indigo-600 text-white'
                                                : 'text-gray-700'
                                                }`}
                                        >
                                            {day.date()}
                                        </div>
                                    </div>

                                    {/* Timeline grid */}
                                    <div
                                        className="relative"
                                        style={{ height: TOTAL_HOURS * HOUR_HEIGHT }}
                                    >
                                        {/* Hour grid lines */}
                                        {Array.from({ length: TOTAL_HOURS }, (_, i) => (
                                            <div
                                                key={HOUR_START + i}
                                                className="absolute w-full border-b border-gray-100"
                                                style={{ top: i * HOUR_HEIGHT, height: HOUR_HEIGHT }}
                                            />
                                        ))}

                                        {/* Current time line */}
                                        {today && showNowLine && (
                                            <div
                                                className="absolute w-full z-10 pointer-events-none"
                                                style={{ top: nowLineTop }}
                                            >
                                                <div className="flex items-center">
                                                    <div className="w-2.5 h-2.5 rounded-full bg-red-500 -ml-1" />
                                                    <div className="flex-1 h-0.5 bg-red-500" />
                                                </div>
                                            </div>
                                        )}

                                        {/* Meeting blocks */}
                                        {positioned.length === 0 && (
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                <Button
                                                    type="dashed"
                                                    icon={<PlusOutlined />}
                                                    size="small"
                                                    className="!text-gray-400"
                                                    onClick={() => handleCreate(day)}
                                                >
                                                    Thêm
                                                </Button>
                                            </div>
                                        )}

                                        {positioned.map((pm) => {
                                            const checkedIn = pm.meeting.participants.filter(
                                                p => p.status === ParticipantStatus.JOINED
                                            ).length;
                                            const total = pm.meeting.participants.length;
                                            const isCompact = pm.height < 50;

                                            return (
                                                <Tooltip
                                                    key={pm.meeting.id}
                                                    title={
                                                        <div>
                                                            <div className="font-semibold">{pm.meeting.title}</div>
                                                            <div className="text-xs opacity-80">
                                                                {dayjs(pm.meeting.start_time).format('HH:mm')} –{' '}
                                                                {dayjs(pm.meeting.end_time).format('HH:mm')}
                                                            </div>
                                                            <div className="text-xs opacity-80">
                                                                Checkin: {checkedIn}/{total}
                                                            </div>
                                                        </div>
                                                    }
                                                    placement="right"
                                                >
                                                    <motion.div
                                                        initial={{ scale: 0.95, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        role="button"
                                                        tabIndex={0}
                                                        className="absolute rounded-lg cursor-pointer transition-all hover:shadow-md hover:scale-[1.02] overflow-hidden"
                                                        style={{
                                                            top: pm.top + 1,
                                                            height: pm.height - 2,
                                                            left: `calc(${pm.left}% + 2px)`,
                                                            width: `calc(${pm.width}% - 4px)`,
                                                            backgroundColor: pm.color.bg,
                                                            borderLeft: `3px solid ${pm.color.border}`,
                                                        }}
                                                        onClick={() => handleMeetingClick(pm.meeting)}
                                                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleMeetingClick(pm.meeting); }}
                                                    >
                                                        <div
                                                            className={`px-2 ${isCompact ? 'py-0.5' : 'py-1.5'} h-full flex flex-col justify-between`}
                                                        >
                                                            <div>
                                                                <Text
                                                                    className={`block font-semibold leading-tight ${isCompact ? 'text-[10px]' : 'text-xs'
                                                                        }`}
                                                                    style={{ color: pm.color.text }}
                                                                    ellipsis
                                                                >
                                                                    {pm.meeting.title}
                                                                </Text>
                                                                {!isCompact && (
                                                                    <Text
                                                                        className="text-[10px] opacity-70 block"
                                                                        style={{ color: pm.color.text }}
                                                                    >
                                                                        <ClockCircleOutlined className="mr-1" />
                                                                        {dayjs(pm.meeting.start_time).format('HH:mm')} –{' '}
                                                                        {dayjs(pm.meeting.end_time).format('HH:mm')}
                                                                    </Text>
                                                                )}
                                                            </div>
                                                            {!isCompact && (
                                                                <div className="flex items-center justify-between mt-1">
                                                                    <span
                                                                        className="text-[10px] flex items-center gap-0.5"
                                                                        style={{ color: pm.color.text }}
                                                                    >
                                                                        <UserOutlined />
                                                                        {checkedIn}/{total}
                                                                    </span>
                                                                    {pm.meeting.require_check_in && (
                                                                        <SafetyCertificateOutlined
                                                                            className="text-[10px]"
                                                                            style={{ color: pm.color.border }}
                                                                        />
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </motion.div>
                                                </Tooltip>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </motion.div>
            )}

            {/* Meeting Detail Drawer */}
            <MeetingDetailDrawer
                key={currentMeeting?.id ?? 'drawer'}
                open={drawerOpen}
                meeting={currentMeeting}
                onClose={() => dispatch({ type: 'CLOSE_DRAWER' })}
                onEdit={handleEdit}
                onDelete={handleDelete}
            />

            {/* Meeting Modal (Create/Edit) */}
            <MeetingModal
                key={editingMeeting?.id ?? 'create'}
                open={modalOpen}
                editingItem={editingMeeting}
                initialDate={modalInitialDate}
                users={users}
                onSubmit={handleSubmit}
                onCancel={() => dispatch({ type: 'CLOSE_MODAL' })}
            />
        </motion.div>
    );
};

export default MeetingCalendarPage;
