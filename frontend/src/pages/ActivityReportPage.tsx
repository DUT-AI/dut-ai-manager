import { useState, useEffect, useCallback, useRef } from 'react';
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
    Row,
    Col,
    Statistic,
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
    ComposedChart,
    Bar,
    Line,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip as RechartsTooltip,
    Legend
} from 'recharts';

const CustomChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    
    const uniquePayload = payload.filter((entry: any, index: number, self: any[]) =>
        index === self.findIndex((e: any) => e.dataKey === entry.dataKey)
    );

    return (
        <div className="bg-white p-3 rounded-xl shadow-lg border border-gray-100">
            <Text strong className="text-xs block mb-2">{label}</Text>
            {uniquePayload.map((entry: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-gray-500">{entry.name}:</span>
                    <span className="font-semibold">{entry.value}</span>
                </div>
            ))}
        </div>
    );
};

const CustomOffsetDot = (props: any) => {
    const { cx, cy, stroke, value, offset, r, fill, strokeWidth } = props;
    if (value === null || value === undefined) return null;
    return (
        <circle cx={cx + offset} cy={cy} r={r || 4} stroke={stroke} strokeWidth={strokeWidth || 2} fill={fill || "white"} />
    );
};

const TrendChart = () => {
    const [allData, setAllData] = useState<ActivityTrendItem[]>([]);
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    const fetchTrend = useCallback(async () => {
        setLoading(true);
        try {
            const now = dayjs();
            const data = await reportService.getActivityTrend(
                now.month() + 1,
                now.year(),
                'week'
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

    // Drag to paginate logic
    const [offset, setOffset] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [startX, setStartX] = useState(0);

    const WEEKS_TO_SHOW = 8;
    const SHIFT_STEP = 4;
    const maxOffset = Math.max(0, allData.length - WEEKS_TO_SHOW);

    const endIndex = allData.length - offset;
    const startIndex = Math.max(0, endIndex - WEEKS_TO_SHOW);
    const currentData = allData.slice(startIndex, endIndex);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        setStartX(e.pageX);
    };

    const handleMouseLeave = () => {
        setIsDragging(false);
    };

    const handleMouseUp = (e: React.MouseEvent) => {
        if (!isDragging) return;
        setIsDragging(false);
        const walk = e.pageX - startX;
        
        if (walk > 50 && offset < maxOffset) {
            setOffset(prev => Math.min(maxOffset, prev + SHIFT_STEP)); // Swipe Right -> Older
        } else if (walk < -50 && offset > 0) {
            setOffset(prev => Math.max(0, prev - SHIFT_STEP)); // Swipe Left -> Newer
        }
    };

    return (
        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mb-8">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-3">
                <div>
                    <Title level={5} className="m-0">Xu hướng Hoạt động</Title>
                    <Text type="secondary" className="text-xs">Theo dõi biến động điểm cộng & vi phạm (Vuốt ngang để xem lịch sử 6 tháng)</Text>
                </div>
            </div>
            <div 
                ref={scrollRef} 
                className={`h-[280px] w-full overflow-hidden ${isDragging ? 'cursor-grabbing' : 'cursor-grab'} select-none`} 
                style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.3s' }}
                onMouseDown={handleMouseDown}
                onMouseLeave={handleMouseLeave}
                onMouseUp={handleMouseUp}
            >
                {allData.length > 0 ? (
                    <div style={{ width: '100%', height: '100%', pointerEvents: isDragging ? 'none' : 'auto' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={currentData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                    dataKey="label"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fontSize: 11, fill: '#94a3b8' }}
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
                                    barSize={20}
                                />
                                <Bar
                                    yAxisId="violation"
                                    dataKey="violation_count"
                                    name="Vi phạm"
                                    fill="#ef4444"
                                    radius={[4, 4, 0, 0]}
                                    barSize={20}
                                />
                                <Line
                                    yAxisId="bonus"
                                    type="monotone"
                                    dataKey="total_bonus_points"
                                    name="Điểm cộng"
                                    className="line-bonus"
                                    stroke="#16a34a"
                                    strokeWidth={2}
                                    dot={<CustomOffsetDot offset={-12} />}
                                    activeDot={<CustomOffsetDot offset={-12} r={6} stroke="#16a34a" />}
                                    legendType="none"
                                />
                                <Line
                                    yAxisId="violation"
                                    type="monotone"
                                    dataKey="violation_count"
                                    name="Vi phạm"
                                    className="line-violation"
                                    stroke="#dc2626"
                                    strokeWidth={2}
                                    dot={<CustomOffsetDot offset={12} />}
                                    activeDot={<CustomOffsetDot offset={12} r={6} stroke="#dc2626" />}
                                    legendType="none"
                                />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        <Text type="secondary">Chưa có dữ liệu cho khoảng thời gian này</Text>
                    </div>
                )}
            </div>
        </motion.div>
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

    const totalPoints = participationData.reduce((sum, item) => sum + (item.total_points || 0), 0);
    const totalBonusPoints = participationData.reduce((sum, item) => sum + (item.total_bonus_points || 0), 0);
    const totalViolations = participationData.reduce((sum, item) => sum + (item.violation_count || 0), 0);
    const avgPoints = participationData.length > 0 ? (totalPoints / participationData.length).toFixed(2) : "0.00";
    const avgBonus = participationData.length > 0 ? (totalBonusPoints / participationData.length).toFixed(2) : "0.00";

    return (
        <>
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="p-4 md:p-6 max-w-7xl mx-auto"
            >


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
                                                {
                                                    title: 'Thành viên', key: 'user', render: (item: ParticipationStats) => (
                                                        <Space>
                                                            <Avatar src={item.user?.avatar_url} icon={<UserOutlined />} />
                                                            <div className="flex flex-col">
                                                                <span>{item.user?.name || `Thành viên #${item.user_id}`}</span>
                                                                <span className="text-xs text-gray-500">{item.user?.email || 'Chưa cập nhật email'}</span>
                                                            </div>
                                                        </Space>
                                                    )
                                                },
                                                { title: 'Giờ hoạt động', key: 'hours', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag color="blue">{item.total_hours}h</Tag> },
                                                { title: 'Buổi tham gia', key: 'sessions', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag>{item.total_sessions} buổi</Tag> },
                                                { title: 'Đúng giờ', key: 'ontime', render: (item: ParticipationStats) => item.total_sessions === 0 ? <Tag>Chưa sinh hoạt</Tag> : <Tag color={item.on_time_rate >= 0.8 ? "success" : "warning"}>{(item.on_time_rate * 100).toFixed(0)}%</Tag> },
                                                { title: 'Điểm cộng', key: 'bonus', render: (item: ParticipationStats) => <Tag color="green">+{item.total_bonus_points ?? 0}</Tag> },
                                                { 
                                                    title: 'Vi phạm', 
                                                    key: 'violations', 
                                                    render: (item: ParticipationStats) => {
                                                        const penalty = (item.late_count || 0) * 2 + (item.absent_count || 0) * 5;
                                                        return <Tag color="red">{penalty > 0 ? `-${penalty}` : 0}</Tag>;
                                                    }
                                                },
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
                                                {
                                                    title: 'Thành viên', key: 'user', render: (item: TitleReportItem) => (
                                                        <Space>
                                                            <Avatar src={item.user?.avatar_url} icon={<UserOutlined />} />
                                                            <div className="flex flex-col">
                                                                <span>{item.user?.name || `Thành viên #${item.user?.id || '?'}`}</span>
                                                                <span className="text-xs text-gray-500">{item.user?.email || 'Chưa cập nhật email'}</span>
                                                            </div>
                                                        </Space>
                                                    )
                                                },
                                                {
                                                    title: 'Danh hiệu', key: 'title', render: (item: TitleReportItem) => (
                                                        item.title ? <TitleBadge title={item.title} /> : <Tag>Chưa có</Tag>
                                                    )
                                                },
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

                <motion.div variants={itemVariants} className="mt-6 mb-8">
                    <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={6}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Tổng điểm của tháng"
                                    value={Math.abs(totalPoints)}
                                    valueStyle={{ color: totalPoints >= 0 ? '#22c55e' : '#ef4444', fontWeight: 'bold' }}
                                    prefix={totalPoints >= 0 ? "+" : "-"}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Tổng điểm cộng"
                                    value={totalBonusPoints}
                                    valueStyle={{ color: '#22c55e', fontWeight: 'bold' }}
                                    prefix="+"
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Tổng vi phạm"
                                    value={totalViolations}
                                    valueStyle={{ color: '#ef4444', fontWeight: 'bold' }}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Điểm trung bình"
                                    value={Math.abs(Number(avgPoints))}
                                    valueStyle={{ color: Number(avgPoints) >= 0 ? '#3b82f6' : '#ef4444', fontWeight: 'bold' }}
                                    prefix={Number(avgPoints) >= 0 ? "+" : "-"}
                                />
                                <Text type="secondary" className="text-xs mt-1">
                                    Điểm cộng TB: <span className="text-green-500 font-semibold">+{avgBonus}</span>
                                </Text>
                            </Card>
                        </Col>
                    </Row>
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
            .line-bonus path.recharts-curve.recharts-line-curve {
                transform: translateX(-12px);
            }
            .line-violation path.recharts-curve.recharts-line-curve {
                transform: translateX(12px);
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
