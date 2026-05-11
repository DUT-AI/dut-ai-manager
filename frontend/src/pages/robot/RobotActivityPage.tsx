import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { meetingService } from '@/services/api/meeting.service';
import { userService } from '@/services/api/user.service';
import { authService } from '@/services/api/auth.service';
import { message, Spin, ConfigProvider, theme, Modal, Table, Tag, Button } from 'antd';
import { MeetingModal } from '@/components/meeting';
import { useNavigate } from 'react-router-dom';
import type { UserResponse } from '@/types/user.types';
import dayjs from 'dayjs';

// Activity Registration - Added Check-in/Out Column and Expiry Logic
const RobotActivityPage = () => {
    const navigate = useNavigate();
    const [selectedBlock, setSelectedBlock] = useState<'morning' | 'afternoon' | 'evening'>('afternoon');
    const [selectedDay, setSelectedDay] = useState(dayjs().date());
    const [meetings, setMeetings] = useState<any[]>([]);
    const [myShifts, setMyShifts] = useState<any[]>([]);
    const [users, setUsers] = useState<UserResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [registeringId, setRegisteringId] = useState<number | null>(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isMyShiftsModalOpen, setIsMyShiftsModalOpen] = useState(false);
    const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
    const [now, setNow] = useState(dayjs());

    // Update 'now' every minute to refresh UI states
    useEffect(() => {
        const interval = setInterval(() => setNow(dayjs()), 60000);
        return () => clearInterval(interval);
    }, []);

    const days = Array.from({ length: 7 }, (_, i) => {
        const d = dayjs().startOf('week').add(i + 1, 'day'); // Mon-Sun
        return {
            name: d.format('ddd'),
            num: d.date(),
            fullDate: d.format('YYYY-MM-DD'),
            isToday: d.isSame(dayjs(), 'day'),
            dimmed: d.day() === 0 || d.day() === 6 // Sun, Sat
        };
    });

    const blocks = [
        { key: 'morning' as const, label: 'Block 01', name: 'Morning', icon: 'wb_sunny' },
        { key: 'afternoon' as const, label: 'Block 02', name: 'Afternoon', icon: 'wb_twilight' },
        { key: 'evening' as const, label: 'Block 03', name: 'Evening', icon: 'bedtime' },
    ];

    const fetchMeetings = async (dateStr: string) => {
        setLoading(true);
        try {
            const res = await meetingService.getMeetingsByDateRange(dateStr, dateStr);
            if (res.is_success) {
                setMeetings(res.data || []);
            }
        } catch (error) {
            message.error('Failed to load activities');
        } finally {
            setLoading(false);
        }
    };

    const fetchMyShifts = async (userId: number) => {
        try {
            const start = dayjs().subtract(7, 'day').format('YYYY-MM-DD');
            const end = dayjs().add(14, 'day').format('YYYY-MM-DD');
            const res = await meetingService.getMeetingsByDateRange(start, end);
            if (res.is_success) {
                const userMeetings = (res.data || []).filter((m: any) => 
                    m.participants?.some((p: any) => p.user_id === userId)
                );
                setMyShifts(userMeetings);
            }
        } catch (error) {
            console.error('Failed to fetch user shifts', error);
        }
    };

    const fetchData = async () => {
        try {
            const [usersRes, profileRes] = await Promise.allSettled([
                userService.getUsers(),
                authService.getMe()
            ]);
            
            if (usersRes.status === 'fulfilled' && usersRes.value.is_success) {
                setUsers(usersRes.value.data || []);
            }
            
            if (profileRes.status === 'fulfilled' && profileRes.value.is_success) {
                const user = profileRes.value.data;
                setCurrentUser(user);
                if (user) fetchMyShifts(user.id);
            }
        } catch (error) {
            console.error('Failed to fetch initial data', error);
        }
    };

    useEffect(() => {
        const activeDay = days.find(d => d.num === selectedDay);
        if (activeDay) {
            fetchMeetings(activeDay.fullDate);
        }
    }, [selectedDay]);

    useEffect(() => {
        fetchData();
    }, []);

    const handleRegister = async (meeting: any) => {
        if (!currentUser) {
            message.error('Please login to register');
            return;
        }

        const isRegistered = meeting.participants?.some((p: any) => p.user_id === currentUser.id);
        if (isRegistered) {
            message.warning('You are already registered for this activity');
            return;
        }

        setRegisteringId(meeting.id);
        try {
            const detailRes = await meetingService.getMeetingById(meeting.id);
            if (!detailRes.is_success) throw new Error('Failed to fetch meeting details');
            
            const currentParticipantIds = detailRes.data.participants?.map((p: any) => p.user_id) || [];
            const updatedUserIds = [...new Set([...currentParticipantIds, currentUser.id])];
            
            const updateRes = await meetingService.updateMeeting(meeting.id, {
                user_ids: updatedUserIds
            });

            if (updateRes.is_success) {
                message.success('Registration successful!');
                const activeDay = days.find(d => d.num === selectedDay);
                if (activeDay) fetchMeetings(activeDay.fullDate);
                fetchMyShifts(currentUser.id);
            }
        } catch (error) {
            message.error('Registration failed. Please try again.');
        } finally {
            setRegisteringId(null);
        }
    };

    const handleCreateMeetingSubmit = async (values: any) => {
        try {
            const res = await meetingService.createMeeting(values);
            if (res.is_success) {
                message.success('Activity created successfully!');
                setIsCreateModalOpen(false);
                const activeDay = days.find(d => d.num === selectedDay);
                if (activeDay) fetchMeetings(activeDay.fullDate);
                if (currentUser) fetchMyShifts(currentUser.id);
            }
        } catch (error) {
            message.error('Failed to create activity');
        }
    };

    const filteredMeetings = meetings.filter(m => {
        const hour = dayjs(m.start_time).hour();
        if (selectedBlock === 'morning') return hour < 12;
        if (selectedBlock === 'afternoon') return hour >= 12 && hour < 18;
        return hour >= 18;
    });

    return (
        <main className="flex-1 p-5 md:p-10 relative">
            <div className="max-w-[1024px] mx-auto w-full relative z-10">
                {/* Header */}
                <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div>
                        <h2 className="font-['Space_Grotesk'] text-[32px] md:text-[48px] leading-[1.1] tracking-[-0.02em] font-bold text-[#e1e2ec] mb-2 text-glow">Activity Registration</h2>
                        <p className="text-[#c2c6d6]">Sync with real-time operational shifts.</p>
                    </div>
                    <button 
                        onClick={() => setIsCreateModalOpen(true)}
                        className="h-[48px] px-6 rounded-xl bg-[#4fdbc8]/10 border border-[#4fdbc8]/30 text-[#4fdbc8] font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-bold uppercase hover:bg-[#4fdbc8]/20 transition-all active:scale-95 flex items-center gap-2 group shadow-[0_0_20px_rgba(79,219,200,0.1)]"
                    >
                        <span className="material-symbols-outlined group-hover:rotate-90 transition-transform">add</span>
                        Create Activity
                    </button>
                </div>

                {/* Calendar Strip */}
                <div className="bg-white/[0.03] backdrop-blur-[12px] border border-white/10 rounded-[24px] p-4 mb-8 overflow-x-auto custom-scrollbar">
                    <div className="flex gap-4 min-w-max">
                        {days.map((day) => (
                            <button
                                key={day.num}
                                onClick={() => setSelectedDay(day.num)}
                                className={`flex flex-col items-center justify-center w-20 h-24 rounded-xl border transition-all cursor-pointer relative ${
                                    day.isToday
                                        ? 'border-[#4fdbc8] bg-[#4fdbc8]/10'
                                        : 'border-[#424754]/20 hover:bg-[#363941]/30'
                                } ${day.dimmed ? 'opacity-50' : ''} ${selectedDay === day.num && !day.isToday ? 'border-[#adc6ff]/50 bg-[#adc6ff]/5' : ''}`}
                            >
                                {day.isToday && (
                                    <div className="absolute -top-2 bg-[#4fdbc8] text-[#003731] px-2 py-0.5 rounded-full font-['JetBrains_Mono'] text-[8px] uppercase font-bold tracking-widest">Today</div>
                                )}
                                <span className={`font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium uppercase mb-1 ${day.isToday ? 'text-[#4fdbc8]' : 'text-[#c2c6d6]'}`}>{day.name}</span>
                                <span className={`font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold ${day.isToday ? 'text-[#4fdbc8] drop-shadow-[0_0_10px_rgba(79,219,200,0.5)]' : 'text-[#e1e2ec]'}`}>{day.num}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Registration Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Time Blocks */}
                    <div className="lg:col-span-3 flex flex-row lg:flex-col gap-4 overflow-x-auto lg:overflow-visible custom-scrollbar">
                        {blocks.map((block) => (
                            <button
                                key={block.key}
                                onClick={() => setSelectedBlock(block.key)}
                                className={`flex-shrink-0 lg:w-full text-left p-4 rounded-xl flex items-center justify-between transition-all relative overflow-hidden ${
                                    selectedBlock === block.key
                                        ? 'bg-white/[0.03] backdrop-blur-[12px] border border-[#4fdbc8]/50 bg-[#4fdbc8]/5 shadow-[0_0_15px_rgba(79,219,200,0.2)]'
                                        : 'bg-[#363941] border border-[#424754]/30 hover:border-[#4fdbc8]/50 group'
                                }`}
                            >
                                {selectedBlock === block.key && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#4fdbc8]" />}
                                <div className={selectedBlock === block.key ? 'pl-2' : ''}>
                                    <div className={`font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium uppercase mb-1 ${selectedBlock === block.key ? 'text-[#4fdbc8]' : 'text-[#c2c6d6]'}`}>{block.label}</div>
                                    <div className={`font-medium ${selectedBlock === block.key ? 'text-[#e1e2ec] drop-shadow-[0_0_10px_rgba(79,219,200,0.5)]' : 'text-[#e1e2ec]'}`}>{block.name}</div>
                                </div>
                                <span className={`material-symbols-outlined ${selectedBlock === block.key ? 'text-[#4fdbc8]' : 'text-[#424754] group-hover:text-[#4fdbc8]'} transition-colors`}
                                    style={selectedBlock === block.key ? { fontVariationSettings: "'FILL' 1" } : undefined}
                                >{block.icon}</span>
                            </button>
                        ))}
                    </div>

                    {/* Event Cards */}
                    <div className="lg:col-span-9 space-y-6 min-h-[400px] relative">
                        {loading && (
                            <div className="absolute inset-0 flex items-center justify-center bg-[#0B1120]/50 backdrop-blur-sm z-20 rounded-[24px]">
                                <Spin size="large" />
                            </div>
                        )}

                        <AnimatePresence mode="popLayout">
                            {filteredMeetings.length > 0 ? (
                                filteredMeetings.map((event, idx) => {
                                    const isRegistered = event.participants?.some((p: any) => p.user_id === currentUser?.id);
                                    const isOver = dayjs(event.end_time).isBefore(now);
                                    
                                    return (
                                        <motion.div
                                            key={event.id}
                                            initial={{ opacity: 0, x: 20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: -20 }}
                                            transition={{ delay: idx * 0.05 }}
                                            className={`bg-white/[0.03] backdrop-blur-[12px] border border-white/10 rounded-[24px] p-6 flex flex-col md:flex-row gap-6 items-start md:items-center relative overflow-hidden group ${isOver ? 'opacity-60' : ''}`}
                                        >
                                            <div className="absolute inset-0 bg-gradient-to-r from-[#4fdbc8]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                            
                                            <div className={`w-16 h-16 rounded-xl border flex items-center justify-center flex-shrink-0 ${isOver ? 'bg-red-500/10 border-red-500/30' : 'bg-[#4d8eff]/20 border-[#4d8eff]/50'}`}>
                                                <span className={`material-symbols-outlined text-3xl ${isOver ? 'text-red-400' : 'text-[#adc6ff]'}`}>
                                                    {isOver ? 'timer_off' : (event.require_check_in ? 'verified_user' : 'event')}
                                                </span>
                                            </div>

                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className={`px-2 py-1 rounded-full border font-['JetBrains_Mono'] text-[10px] uppercase ${isOver ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-[#4fdbc8]/10 border-[#4fdbc8]/20 text-[#4fdbc8]'}`}>
                                                        {dayjs(event.start_time).format('HH:mm')} - {dayjs(event.end_time).format('HH:mm')}
                                                    </span>
                                                    {isRegistered && (
                                                        <span className="px-2 py-1 rounded-full bg-[#4fdbc8]/20 text-[#4fdbc8] border border-[#4fdbc8]/30 font-['JetBrains_Mono'] text-[10px] uppercase font-bold">
                                                            Registered
                                                        </span>
                                                    )}
                                                </div>
                                                <h3 className={`font-['Space_Grotesk'] text-[24px] leading-[1.2] font-semibold mb-1 ${isOver ? 'text-gray-500' : 'text-[#e1e2ec]'}`}>{event.title}</h3>
                                                <div className="flex items-center gap-2 text-[#c2c6d6] text-sm">
                                                    <span className="material-symbols-outlined text-[16px]">group</span>
                                                    <span>{event.participants?.length || 0} Participants</span>
                                                </div>
                                            </div>

                                            <div className="w-full md:w-auto mt-4 md:mt-0 flex-shrink-0 z-10">
                                                {isOver ? (
                                                    <div className="flex items-center gap-2 text-red-400/70 font-['JetBrains_Mono'] text-[12px] uppercase tracking-wider italic">
                                                        <span className="material-symbols-outlined text-[18px]">info</span>
                                                        The meeting is over
                                                    </div>
                                                ) : (
                                                    <button 
                                                        onClick={() => handleRegister(event)}
                                                        disabled={registeringId === event.id || isRegistered}
                                                        className={`w-full md:w-auto h-[44px] px-8 rounded-xl font-['JetBrains_Mono'] text-[12px] tracking-[0.1em] font-medium uppercase transition-all flex items-center justify-center gap-2 ${
                                                            isRegistered 
                                                                ? 'bg-[#4fdbc8]/20 text-[#4fdbc8] border border-[#4fdbc8]/30 cursor-not-allowed opacity-80'
                                                                : 'bg-[#adc6ff] text-[#002e6a] hover:bg-[#adc6ff]/80 shadow-[0_0_15px_rgba(173,198,255,0.3)] active:scale-95'
                                                        }`}
                                                    >
                                                        {registeringId === event.id ? (
                                                            <Spin size="small" />
                                                        ) : isRegistered ? (
                                                            <>
                                                                <span className="material-symbols-outlined text-[18px]">check_circle</span>
                                                                Joined
                                                            </>
                                                        ) : (
                                                            'Register'
                                                        )}
                                                    </button>
                                                )}
                                            </div>
                                        </motion.div>
                                    );
                                })
                            ) : (
                                !loading && (
                                    <motion.div 
                                        initial={{ opacity: 0 }} 
                                        animate={{ opacity: 1 }}
                                        className="flex flex-col items-center justify-center py-20 text-[#424754]"
                                    >
                                        <span className="material-symbols-outlined text-6xl mb-4">event_busy</span>
                                        <p className="font-['JetBrains_Mono'] text-[14px] uppercase tracking-widest">No activities scheduled for this block.</p>
                                    </motion.div>
                                )
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                <div className="h-24 w-full" />
            </div>

            {/* Ant Design ConfigProvider for PERFECT Dark Theme Isolation */}
            <ConfigProvider
                theme={{
                    algorithm: theme.darkAlgorithm,
                    token: {
                        colorPrimary: '#4fdbc8',
                        colorBgBase: '#000000',
                        colorBgElevated: '#0b1120',
                        colorBgContainer: '#000000',
                        colorTextBase: '#ffffff',
                        colorText: '#ffffff',
                        colorBorder: 'rgba(79, 219, 200, 0.4)',
                        borderRadius: 16,
                    },
                    components: {
                        Modal: {
                            headerBg: '#000000',
                            contentBg: '#000000',
                            footerBg: '#000000',
                        },
                        Select: {
                            selectorBg: '#000000',
                        },
                        Input: {
                            activeBg: '#000000',
                        },
                        Table: {
                            headerBg: '#1a1f2e',
                            headerColor: '#4fdbc8',
                            colorBgContainer: '#000000',
                        }
                    }
                }}
            >
                <MeetingModal
                    open={isCreateModalOpen}
                    initialDate={dayjs().date(selectedDay)}
                    users={users}
                    onSubmit={handleCreateMeetingSubmit}
                    onCancel={() => setIsCreateModalOpen(false)}
                />

                <Modal
                    title={<span className="font-['Space_Grotesk'] text-2xl font-bold text-[#4fdbc8]">My Registered Shifts</span>}
                    open={isMyShiftsModalOpen}
                    onCancel={() => setIsMyShiftsModalOpen(false)}
                    footer={null}
                    width={900}
                    centered
                >
                    <Table 
                        dataSource={myShifts} 
                        rowKey="id"
                        pagination={false}
                        className="robot-table"
                        locale={{ emptyText: <span className="text-[#424754]">No upcoming shifts found.</span> }}
                    >
                        <Table.Column 
                            title="ACTIVITY" 
                            dataIndex="title" 
                            key="title"
                            render={(text, record: any) => (
                                <div>
                                    <div className="text-white font-medium">{text}</div>
                                    <div className="text-[10px] text-[#c2c6d6]">{dayjs(record.start_time).format('DD/MM/YYYY')}</div>
                                </div>
                            )}
                        />
                        <Table.Column 
                            title="TIME" 
                            key="time"
                            render={(_, record: any) => (
                                <Tag color="blue" className="bg-[#adc6ff]/10 border-[#adc6ff]/30 text-[#adc6ff]">
                                    {dayjs(record.start_time).format('HH:mm')} - {dayjs(record.end_time).format('HH:mm')}
                                </Tag>
                            )}
                        />
                        <Table.Column 
                            title="CHECK-IN/OUT" 
                            key="action"
                            render={(_, record: any) => {
                                const start = dayjs(record.start_time);
                                const end = dayjs(record.end_time);
                                const isOver = now.isAfter(end);
                                const isActive = now.isAfter(start.subtract(30, 'minute')) && now.isBefore(end);

                                if (isOver) {
                                    return <span className="text-red-400/50 text-[10px] uppercase font-bold italic">Expired</span>;
                                }

                                if (isActive) {
                                    return (
                                        <Button 
                                            type="primary" 
                                            size="small"
                                            onClick={() => navigate('/dashboard/robot/checker')}
                                            className="bg-[#4fdbc8] text-black border-none hover:opacity-80 flex items-center gap-1 h-8 rounded-lg px-4"
                                        >
                                            <span className="material-symbols-outlined text-[16px]">login</span>
                                            <span className="text-[11px] font-bold uppercase tracking-wider">Check-in Now</span>
                                        </Button>
                                    );
                                }

                                return <span className="text-[#c2c6d6]/40 text-[10px] uppercase font-bold tracking-widest">Awaiting Time</span>;
                            }}
                        />
                        <Table.Column 
                            title="STATUS" 
                            key="status"
                            render={() => (
                                <Tag color="success" className="bg-[#4fdbc8]/10 border-[#4fdbc8]/30 text-[#4fdbc8] font-bold text-[10px]">
                                    REGISTERED
                                </Tag>
                            )}
                        />
                    </Table>
                </Modal>
            </ConfigProvider>

            {/* FAB */}
            <div className="fixed bottom-10 right-10 z-[9999]">
                <button 
                    onClick={() => setIsMyShiftsModalOpen(true)}
                    className="flex items-center gap-3 bg-[#4fdbc8] text-[#003731] h-16 pl-8 pr-10 rounded-full shadow-[0_0_30px_rgba(79,219,200,0.5)] hover:shadow-[0_0_50px_rgba(79,219,200,0.7)] transition-all active:scale-95 group hover:-translate-y-1"
                >
                    <span className="material-symbols-outlined text-3xl group-hover:rotate-12 transition-transform">event_available</span>
                    <span className="font-['JetBrains_Mono'] text-[14px] tracking-[0.1em] font-black uppercase">My Registered Shifts</span>
                </button>
            </div>

            <style>{`
                .text-glow {
                    text-shadow: 0 0 15px rgba(225, 226, 236, 0.3);
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                    height: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(79, 219, 200, 0.1);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(79, 219, 200, 0.3);
                }

                /* Additional CSS overrides to force Robot styling on top of antd dark theme */
                .ant-modal-root .ant-modal-content {
                    border: 2px solid #4fdbc8 !important;
                    box-shadow: 0 0 50px rgba(0, 0, 0, 1), 0 0 30px rgba(79, 219, 200, 0.2) !important;
                    border-radius: 28px !important;
                }

                .ant-modal-root .ant-modal-title {
                    color: #4fdbc8 !important;
                    font-family: 'Space Grotesk', sans-serif !important;
                    font-weight: 800 !important;
                    font-size: 26px !important;
                    text-shadow: 0 0 10px rgba(79, 219, 200, 0.3) !important;
                }

                .ant-modal-root .ant-form-item-label > label {
                    color: #fef3c7 !important;
                    font-family: 'JetBrains Mono', monospace !important;
                    font-size: 12px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.15em !important;
                }

                .ant-modal-root .ant-select-selector,
                .ant-modal-root .ant-input,
                .ant-modal-root .ant-picker {
                    border: 1px solid rgba(255, 255, 255, 0.4) !important;
                    height: 52px !important;
                    display: flex !important;
                    align-items: center !important;
                }

                .ant-modal-root .ant-btn-primary {
                    background: #4fdbc8 !important;
                    color: #000000 !important;
                    height: 50px !important;
                    border-radius: 16px !important;
                    font-weight: 900 !important;
                    font-family: 'JetBrains Mono', monospace !important;
                }

                /* Table Styling */
                .robot-table .ant-table {
                    background: transparent !important;
                }
                .robot-table .ant-table-thead > tr > th {
                    border-bottom: 1px solid rgba(79, 219, 200, 0.2) !important;
                    font-family: 'JetBrains Mono', monospace !important;
                    font-size: 11px !important;
                    letter-spacing: 0.1em !important;
                    text-transform: uppercase;
                }
                .robot-table .ant-table-tbody > tr > td {
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
                }
                .robot-table .ant-table-tbody > tr:hover > td {
                    background: rgba(79, 219, 200, 0.05) !important;
                }
            `}</style>
        </main>
    );
};

export default RobotActivityPage;
