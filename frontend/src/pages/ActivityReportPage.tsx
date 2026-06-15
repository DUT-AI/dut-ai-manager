import { useState, useEffect, useCallback } from 'react';
import {
    Card,
    Tabs,
    Table,
    Typography,
    Space,
    Input,
    Tag,
    Avatar,
    Grid,
} from 'antd';
import {
    SearchOutlined,
    UserOutlined,
    BarChartOutlined,
    CrownOutlined,
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/services/api/report.service';
import type { TitleReportItem, ParticipationStats, ActivityTrendItem } from '@/types/report.types';
import { useDebounce } from '@/hooks/useDebounce';
import { motion, AnimatePresence, type Variants } from 'motion/react';
import { TitleBadge } from '@/components/UserTitleBadge';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

import { Agentation } from 'agentation';

import { 
    ResponsiveContainer, 
    BarChart,
    Bar,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip as RechartsTooltip,
    Legend
} from 'recharts';

// --- Custom Tooltip for BarChart ---
const CustomChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white p-3 rounded-xl shadow-lg border border-gray-100">
            <Text strong className="text-xs block mb-2">{label}</Text>
            {payload.map((entry: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-gray-500">{entry.name}:</span>
                    <span className="font-semibold">{entry.value}</span>
                </div>
            ))}
        </div>
    );
};

// --- TrendChart: BarChart showing monthly aggregation only ---
const TrendChart = () => {
    const [allData, setAllData] = useState<ActivityTrendItem[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchTrend = useCallback(async () => {
        setLoading(true);
        try {
            const now = dayjs();
            const data = await reportService.getActivityTrend(
                now.month() + 1,
                now.year(),
                'month'
            );
            setAllData(data || []);
        } catch (error) {
            console.error('Failed to fetch activity trend:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTrend();
    }, [fetchTrend]);

    return (
        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mb-8">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-3">
                <div>
                    <Title level={5} className="m-0">Xu hướng Hoạt động</Title>
                    <Text type="secondary" className="text-xs">Theo dõi biến động điểm cộng & vi phạm theo tháng</Text>
                </div>
            </div>
            <div className="h-[280px] w-full" style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.3s' }}>
                {allData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={allData} margin={{ top: 5, right: 60, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis
                                dataKey="label"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 12, fill: '#94a3b8' }}
                                dy={10}
                            />
                            {/* Left Y-axis: Bonus Points */}
                            <YAxis
                                yAxisId="bonus"
                                orientation="left"
                                domain={[0, 'dataMax']}
                                tickFormatter={(v: number) => `+${v}`}
                                stroke="#22c55e"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 11, fill: '#22c55e' }}
                            />
                            {/* Right Y-axis: Violations */}
                            <YAxis
                                yAxisId="violation"
                                orientation="right"
                                domain={[0, 'dataMax']}
                                stroke="#ef4444"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 11, fill: '#ef4444' }}
                            />
                            <RechartsTooltip content={<CustomChartTooltip />} />
                            <Legend
                                iconType="circle"
                                wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                            />
                            <Bar
                                yAxisId="bonus"
                                dataKey="total_bonus_points"
                                name="Điểm cộng"
                                fill="#22c55e"
                                radius={[4, 4, 0, 0]}
                                barSize={32}
                            />
                            <Bar
                                yAxisId="violation"
                                dataKey="violation_count"
                                name="Vi phạm"
                                fill="#ef4444"
                                radius={[4, 4, 0, 0]}
                                barSize={32}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        <Text type="secondary">Chưa có dữ liệu cho khoảng thời gian này</Text>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

const LeaderboardHero = ({ data }: { data: any[] }) => {
    // Sort by points to ensure correct ranking even if API returns unsorted
    const top3 = [...data].sort((a, b) => (b.total_points || 0) - (a.total_points || 0)).slice(0, 3);

    return (
        <AnimatePresence>
            {top3.length > 0 && (
                <motion.div 
                    key="leaderboard-hero"
                    initial={{ opacity: 0, y: -20, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -20, height: 0 }}
                    transition={{ duration: 0.4, ease: "easeInOut" }}
                    className="bg-gradient-to-br from-orange-500 to-amber-400 rounded-3xl p-6 md:p-8 mb-8 text-white shadow-xl shadow-orange-200 relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-8 opacity-10">
                        <CrownOutlined style={{ fontSize: '120px' }} />
                    </div>
            
            <div className="relative z-10">
                <Title level={4} className="text-white opacity-80 mb-6 uppercase tracking-wider text-xs font-bold">Bảng vinh danh tháng này</Title>
                
                <div className="flex flex-col md:flex-row items-center justify-around gap-8">
                    {/* Rank 2 */}
                    {top3[1] && (
                        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="flex flex-col items-center order-2 md:order-1">
                            <div className="relative mb-3">
                                <Avatar size={70} src={top3[1].user?.avatar_url} className="border-4 border-white/30 shadow-lg" />
                                <div className="absolute -bottom-2 -right-2 bg-gray-300 text-gray-700 w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 border-white text-xs">2</div>
                            </div>
                            <Text strong className="text-white text-sm">{top3[1].user?.name}</Text>
                            <div className="flex flex-col items-center">
                                <Text className="text-white/70 text-[10px]">+{top3[1].total_points} pts</Text>
                                {top3[1].title && <div className="scale-75 origin-top mt-1"><TitleBadge title={top3[1].title} /></div>}
                            </div>
                        </motion.div>
                    )}

                    {/* Rank 1 */}
                    {top3[0] && (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center order-1 md:order-2 scale-110">
                            <div className="relative mb-4">
                                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-amber-200 animate-bounce">
                                    <CrownOutlined style={{ fontSize: '24px' }} />
                                </div>
                                <Avatar size={90} src={top3[0].user?.avatar_url} className="border-4 border-amber-200 shadow-2xl shadow-orange-900/20" />
                                <div className="absolute -bottom-2 -right-2 bg-amber-400 text-white w-10 h-10 rounded-full flex items-center justify-center font-bold border-2 border-white text-lg">1</div>
                            </div>
                            <Text strong className="text-white text-lg">{top3[0].user?.name}</Text>
                            <div className="flex flex-col items-center">
                                <Text className="text-amber-100 font-medium">+{top3[0].total_points} pts</Text>
                                {top3[0].title && <div className="mt-1"><TitleBadge title={top3[0].title} /></div>}
                            </div>
                        </motion.div>
                    )}

                    {/* Rank 3 */}
                    {top3[2] && (
                        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }} className="flex flex-col items-center order-3 md:order-3">
                            <div className="relative mb-3">
                                <Avatar size={70} src={top3[2].user?.avatar_url} className="border-4 border-white/30 shadow-lg" />
                                <div className="absolute -bottom-2 -right-2 bg-orange-300 text-orange-900 w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 border-white text-xs">3</div>
                            </div>
                            <Text strong className="text-white text-sm">{top3[2].user?.name}</Text>
                            <div className="flex flex-col items-center">
                                <Text className="text-white/70 text-[10px]">+{top3[2].total_points} pts</Text>
                                {top3[2].title && <div className="scale-75 origin-top mt-1"><TitleBadge title={top3[2].title} /></div>}
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
        )}
        </AnimatePresence>
    );
};

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

const RankBadge = ({ rank }: { rank: number }) => {
    if (rank === 1) return <Tag color="gold" className="text-base px-2 py-0.5 m-0">#1 🏆</Tag>;
    if (rank === 2) return <Tag color="geekblue" className="text-base px-2 py-0.5 m-0">#2 🥈</Tag>;
    if (rank === 3) return <Tag color="cyan" className="text-base px-2 py-0.5 m-0">#3 🥉</Tag>;
    return <span className="text-gray-500 font-semibold text-lg">#{rank}</span>;
};

const ActivityReportPage = () => {
    const [activeTab, setActiveTab] = useState<'participation' | 'title'>('participation');
    const [loading, setLoading] = useState(false);
    const [titleData, setTitleData] = useState<TitleReportItem[]>([]);
    const [leaderboardData, setLeaderboardData] = useState<TitleReportItem[]>([]);
    const [participationData, setParticipationData] = useState<ParticipationStats[]>([]);

    const [searchText, setSearchText] = useState('');
    const debouncedSearchText = useDebounce(searchText, 500);

    // Pagination state for correct ranking across pages
    const [participationPage, setParticipationPage] = useState(1);
    const [titlePage, setTitlePage] = useState(1);
    const PAGE_SIZE = 10;

    // Dedicated function to fetch title data for the persistent leaderboard
    const fetchLeaderboardData = async () => {
        try {
            const targetMonth = dayjs().month() + 1;
            const targetYear = dayjs().year();
            const titles = await reportService.getTitlesReport(targetMonth, targetYear);
            setLeaderboardData(titles || []);
            // Also sync titleData if we are on the title tab
            if (activeTab === 'title') {
                setTitleData(titles || []);
            }
        } catch (error) {
            console.error("Failed to fetch leaderboard data", error);
        }
    };

    const fetchData = async () => {
        setLoading(true);
        try {
            const targetMonth = dayjs().month() + 1;
            const targetYear = dayjs().year();

            if (activeTab === 'title') {
                // If on title tab, we use the already fetched or newly fetched leaderboard data
                await fetchLeaderboardData();
            } else if (activeTab === 'participation') {
                const participation = await reportService.getParticipationLeaderboard(targetMonth, targetYear);
                setParticipationData(participation || []);
            }
        } catch (error) {
            console.error("Failed to fetch report data", error);
        } finally {
            setLoading(false);
        }
    };

    // Initial load: always fetch leaderboard data
    useEffect(() => {
        fetchLeaderboardData();
    }, []);

    // Fetch tab-specific data when tab or search changes
    useEffect(() => {
        fetchData();
    }, [activeTab, debouncedSearchText]);

    // Filter data by search text
    const filteredParticipationData = participationData.filter(item => {
        if (!debouncedSearchText) return true;
        const name = item.user?.name?.toLowerCase() || '';
        const email = item.user?.email?.toLowerCase() || '';
        const search = debouncedSearchText.toLowerCase();
        return name.includes(search) || email.includes(search);
    });

    const filteredTitleData = titleData.filter(item => {
        if (!debouncedSearchText) return true;
        const name = item.user?.name?.toLowerCase() || '';
        const email = item.user?.email?.toLowerCase() || '';
        const search = debouncedSearchText.toLowerCase();
        return name.includes(search) || email.includes(search);
    });

    const screens = useBreakpoint();

    return (
        <>
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6 max-w-7xl mx-auto"
        >
            {/* The Hall of Fame now ALWAYS uses leaderboardData (Title-based) */}
            <LeaderboardHero data={leaderboardData} />
            
            <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                <Space size="middle">
                    <div className="hidden md:flex w-12 h-12 rounded-xl bg-orange-50 items-center justify-center text-orange-600 shadow-sm">
                        <BarChartOutlined className="text-2xl" />
                    </div>
                    <div>
                        <Title level={3} className="text-xl md:text-2xl mt-4 text-orange-600">Báo cáo Hoạt động</Title>
                        <Text type="secondary" className="text-xs md:text-sm">Xem thống kê tham gia hoạt động và bảng xếp hạng</Text>
                    </div>
                </Space>
                <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                    <Input
                        prefix={<SearchOutlined className="text-gray-400" />}
                        placeholder="Tìm thành viên..."
                        value={searchText}
                        onChange={e => setSearchText(e.target.value)}
                        allowClear
                        className="w-full sm:w-64"
                    />
                </div>
            </motion.div>

            <motion.div variants={itemVariants}>
                <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-xs border-none bg-white/80 backdrop-blur-md"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                    <Tabs
                        activeKey={activeTab}
                        onChange={(key) => setActiveTab(key as any)}
                        tabBarStyle={{ padding: !screens.md ? '0 12px' : '0 24px', margin: 0, borderBottom: '1px solid #f1f5f9' }}
                        size="large"
                        className="custom-report-tabs"
                        items={[
                            {
                                key: 'participation',
                                label: (
                                    <Space>
                                        <CalendarOutlined />
                                        <span>Điểm danh</span>
                                    </Space>
                                ),
                                children: (
                                    <Table
                                        columns={[
                                            { title: 'Xếp hạng', key: 'rank', render: (_, __, index) => <RankBadge rank={(participationPage - 1) * PAGE_SIZE + index + 1} />, width: 80 },
                                            { title: 'Thành viên', key: 'user', render: (item: ParticipationStats) => (
                                                <Space>
                                                    <Avatar src={item.user?.avatar_url} icon={<UserOutlined />} />
                                                    <div className="flex flex-col">
                                                        <span>{item.user?.name || `Thành viên #${item.user_id}`}</span>
                                                        <span className="text-xs text-gray-500">{item.user?.email || 'Chưa cập nhật email'}</span>
                                                    </div>
                                                </Space>
                                            )},
                                            { title: 'Giờ hoạt động', key: 'hours', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag color="blue">{item.total_hours}h</Tag> },
                                            { title: 'Buổi tham gia', key: 'sessions', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag>{item.total_sessions} buổi</Tag> },
                                            { title: 'Đúng giờ', key: 'ontime', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag color={item.on_time_rate >= 0.8 ? "success" : "warning"}>{(item.on_time_rate * 100).toFixed(0)}%</Tag> },
                                            { title: 'Điểm cộng', key: 'bonus', render: (item: ParticipationStats) => <Tag color="green">+{item.total_bonus_points ?? 0}</Tag> },
                                            { title: 'Vi phạm', key: 'violations', render: (item: ParticipationStats) => <Tag color="red">{item.violation_count ?? 0}</Tag> },
                                            { title: 'Điểm tổng', key: 'total', render: (item: ParticipationStats) => <Tag color={item.total_points > 0 ? "success" : item.total_points < 0 ? "error" : "default"} className="font-bold">{item.total_points > 0 ? `+${item.total_points}` : item.total_points}</Tag> },
                                        ]}
                                        dataSource={filteredParticipationData}
                                        rowKey={(record) => record.user_id}
                                        loading={loading}
                                        pagination={{
                                            pageSize: PAGE_SIZE,
                                            current: participationPage,
                                            onChange: (page) => setParticipationPage(page),
                                        }}
                                        className="p-4"
                                    />
                                )
                            },

                            {
                                key: 'title',
                                label: (
                                    <Space>
                                        <CrownOutlined />
                                        <span>Danh hiệu</span>
                                    </Space>
                                ),
                                children: (
                                    <Table
                                        columns={[
                                            { title: 'Xếp hạng', key: 'rank', render: (_, __, index) => <RankBadge rank={(titlePage - 1) * PAGE_SIZE + index + 1} />, width: 80 },
                                            { title: 'Thành viên', key: 'user', render: (item: TitleReportItem) => (
                                                <Space>
                                                    <Avatar src={item.user?.avatar_url} icon={<UserOutlined />} />
                                                    <div className="flex flex-col">
                                                        <span>{item.user?.name || `Thành viên #${item.user?.id || '?'}`}</span>
                                                        <span className="text-xs text-gray-500">{item.user?.email || 'Chưa cập nhật email'}</span>
                                                    </div>
                                                </Space>
                                            )},
                                            { title: 'Danh hiệu', key: 'title', render: (item: TitleReportItem) => (
                                                item.title ? <TitleBadge title={item.title} /> : <Tag>Chưa có</Tag>
                                            )},
                                            { title: 'Điểm tích lũy', key: 'points', render: (item: TitleReportItem) => <Tag color="green">+{item.total_points}</Tag> },
                                            { title: 'Vi phạm', key: 'violations', render: (item: TitleReportItem) => <Tag color="red">{item.violation_count}</Tag> },
                                        ]}
                                        dataSource={filteredTitleData}
                                        rowKey={(record) => record.user?.id}
                                        loading={loading}
                                        pagination={{
                                            pageSize: PAGE_SIZE,
                                            current: titlePage,
                                            onChange: (page) => setTitlePage(page),
                                        }}
                                        className="p-4"
                                    />
                                )
                            },
                        ]}
                    />
                </Card>
            </motion.div>

            <div className="mt-12">
                <TrendChart />
            </div>
        </motion.div>
        <style>{`
            .custom-report-tabs .ant-tabs-nav::before {
                display: none;
            }
            .custom-report-tabs .ant-tabs-tab {
                padding: 16px 0 !important;
                margin-right: 32px !important;
                transition: all 0.3s ease;
            }
            .custom-report-tabs .ant-tabs-tab-active .ant-tabs-tab-btn {
                color: #f97316 !important;
                font-weight: 600;
            }
            .custom-report-tabs .ant-tabs-ink-bar {
                background: #f97316 !important;
                height: 3px !important;
                border-radius: 3px 3px 0 0;
            }
            .ant-table-thead > tr > th {
                background: #fcfcfd !important;
                color: #64748b !important;
                font-size: 12px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.025em !important;
                font-weight: 700 !important;
                border-bottom: 1px solid #f1f5f9 !important;
            }
            .ant-table-tbody > tr > td {
                border-bottom: 1px solid #f8fafc !important;
                padding: 16px !important;
            }
            .ant-table-tbody > tr:hover > td {
                background: #fffaf5 !important;
            }
        `}</style>
        <Agentation />
        </>
    );
};

export default ActivityReportPage;
