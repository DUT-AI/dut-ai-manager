import { useState, useEffect } from 'react';
import {
    Card,
    Tabs,
    Table,
    Typography,
    Space,
    Input,
    DatePicker,
    Tag,
    Avatar,
    Grid,
    List
} from 'antd';
import {
    SearchOutlined,
    TrophyOutlined,
    WarningOutlined,
    UserOutlined,
    BarChartOutlined,
    CrownOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/services/api/report.service';
import type { ReportItem, ReportResponse, TitleReportItem } from '@/types/report.types';
import type { ColumnsType } from 'antd/es/table';
import { useDebounce } from '@/hooks/useDebounce';
import { motion, type Variants } from 'motion/react';
import { TitleBadge } from '@/components/UserTitleBadge';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

import { 
    ResponsiveContainer, 
    AreaChart, 
    Area,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip
} from 'recharts';

// --- Components for Premium UI ---

const TrendChart = ({ data }: { data: any[] }) => {
    const chartData = [
        { name: 'Tuần 1', points: 400, violations: 24 },
        { name: 'Tuần 2', points: 300, violations: 13 },
        { name: 'Tuần 3', points: 200, violations: 98 },
        { name: 'Tuần 4', points: 278, violations: 39 },
    ];

    return (
        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm mb-8">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <Title level={5} className="m-0">Xu hướng Hoạt động</Title>
                    <Text type="secondary" className="text-xs">Theo dõi biến động điểm số qua các tuần</Text>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                        <Text className="text-xs">Điểm Bonus</Text>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-400"></div>
                        <Text className="text-xs">Vi phạm</Text>
                    </div>
                </div>
            </div>
            <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorPoints" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f97316" stopOpacity={0.1}/>
                                <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis 
                            dataKey="name" 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{ fontSize: 12, fill: '#94a3b8' }}
                            dy={10}
                        />
                        <YAxis 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{ fontSize: 12, fill: '#94a3b8' }}
                        />
                        <Tooltip 
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                        />
                        <Area 
                            type="monotone" 
                            dataKey="points" 
                            stroke="#f97316" 
                            strokeWidth={3}
                            fillOpacity={1} 
                            fill="url(#colorPoints)" 
                        />
                        <Area 
                            type="monotone" 
                            dataKey="violations" 
                            stroke="#f87171" 
                            strokeWidth={3}
                            fill="transparent"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </motion.div>
    );
};

const QuickStats = ({ data }: { data: any[] }) => {
    const totalPoints = data.reduce((acc, item) => acc + (item.total_points || 0), 0);
    const totalViolations = data.reduce((acc, item) => acc + (item.total_violations || 0), 0);
    const avgPoints = data.length > 0 ? (totalPoints / data.length).toFixed(1) : 0;

    const stats = [
        {
            title: 'Tổng điểm Bonus',
            value: `+${totalPoints}`,
            icon: <TrophyOutlined className="text-orange-500" />,
            color: 'bg-orange-50',
            trend: '+12% so với tháng trước',
            trendColor: 'text-green-500'
        },
        {
            title: 'Tổng số Vi phạm',
            value: totalViolations,
            icon: <WarningOutlined className="text-red-500" />,
            color: 'bg-red-50',
            trend: '-5% so với tháng trước',
            trendColor: 'text-green-500'
        },
        {
            title: 'Điểm trung bình',
            value: `+${avgPoints}`,
            icon: <BarChartOutlined className="text-blue-500" />,
            color: 'bg-blue-50',
            trend: 'Ổn định',
            trendColor: 'text-gray-400'
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {stats.map((stat, idx) => (
                <motion.div
                    key={idx}
                    whileHover={{ y: -5 }}
                    className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center justify-between"
                >
                    <div>
                        <Text type="secondary" className="text-xs font-medium uppercase mb-1 block">{stat.title}</Text>
                        <Title level={2} className="m-0 text-2xl font-bold">{stat.value}</Title>
                        <Text className={`text-[10px] mt-1 block ${stat.trendColor}`}>{stat.trend}</Text>
                    </div>
                    <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center text-xl shadow-inner`}>
                        {stat.icon}
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

const LeaderboardHero = ({ data }: { data: any[] }) => {
    // Sort by points to ensure correct ranking even if API returns unsorted
    const top3 = [...data].sort((a, b) => (b.total_points || 0) - (a.total_points || 0)).slice(0, 3);
    if (top3.length === 0) return null;

    return (
        <div className="bg-gradient-to-br from-orange-500 to-amber-400 rounded-3xl p-6 md:p-8 mb-8 text-white shadow-xl shadow-orange-200 relative overflow-hidden">
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
        </div>
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

interface MobileListViewProps {
    data: ReportItem[];
    loading: boolean;
    activeTab: string;
}

const MobileListView = ({ data, loading, activeTab }: MobileListViewProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={data}
            loading={loading}
            split={false}
            renderItem={(item) => (
                <List.Item className="px-2 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <RankBadge rank={item.rank} />
                            <Tag className="m-0">{item.details_count} records</Tag>
                        </div>
                        <div className="flex items-center gap-3 mb-5">
                            <Avatar size={48} src={item.user?.avatar_url} icon={<UserOutlined />} className="shrink-0" />
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="truncate text-base">{item.user?.name || 'Unknown'}</Text>
                                <Text type="secondary" className="text-xs truncate">{item.user?.email}</Text>
                            </div>
                        </div>
                        <div className="flex justify-between items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3">
                            <Text type="secondary" className="text-sm">Total {activeTab === 'bonus' ? 'Points' : 'Violations'}</Text>
                            <Text strong className="text-xl leading-none" type={activeTab === 'bonus' ? 'success' : 'danger'}>
                                {activeTab === 'bonus' ? `+${item.total_points}` : item.total_violations}
                            </Text>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

interface DesktopTableViewProps {
    columns: ColumnsType<ReportItem>;
    data: ReportItem[];
    loading: boolean;
}

const DesktopTableView = ({ columns, data, loading }: DesktopTableViewProps) => (
    <Table
        columns={columns}
        dataSource={data}
        rowKey={(record) => record.user?.id || Math.random()}
        loading={loading}
        pagination={{ pageSize: 10 }}
        className="p-4"
    />
);

const ActivityReportPage = () => {
    const [activeTab, setActiveTab] = useState<'bonus' | 'violation' | 'title'>('bonus');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<ReportItem[]>([]);
    const [titleData, setTitleData] = useState<TitleReportItem[]>([]);
    const [leaderboardData, setLeaderboardData] = useState<TitleReportItem[]>([]);

    const [selectedDate, setSelectedDate] = useState<dayjs.Dayjs | null>(null);
    const [searchText, setSearchText] = useState('');
    const debouncedSearchText = useDebounce(searchText, 500);

    // Dedicated function to fetch title data for the persistent leaderboard
    const fetchLeaderboardData = async () => {
        try {
            const targetMonth = selectedDate ? selectedDate.month() + 1 : dayjs().month() + 1;
            const targetYear = selectedDate ? selectedDate.year() : dayjs().year();
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
            const month = selectedDate ? selectedDate.month() + 1 : undefined;
            const year = selectedDate ? selectedDate.year() : undefined;

            if (activeTab === 'title') {
                // If on title tab, we use the already fetched or newly fetched leaderboard data
                await fetchLeaderboardData();
            } else {
                let response: ReportResponse;
                if (activeTab === 'bonus') {
                    response = await reportService.getBonusPointReport(month, year, debouncedSearchText);
                } else {
                    response = await reportService.getViolationReport(month, year, debouncedSearchText);
                }
                setData(response.items || []);
            }
        } catch (error) {
            console.error("Failed to fetch report data", error);
        } finally {
            setLoading(false);
        }
    };

    // Initial load and when date changes: always fetch leaderboard data
    useEffect(() => {
        fetchLeaderboardData();
    }, [selectedDate]);

    // Fetch tab-specific data when tab or search changes
    useEffect(() => {
        fetchData();
    }, [activeTab, selectedDate, debouncedSearchText]);

    const columns = [
        {
            title: 'Rank',
            dataIndex: 'rank',
            key: 'rank',
            width: 80,
            render: (rank: number) => {
                if (rank === 1) return <Tag color="gold" className="text-base px-3 py-1">#1 🏆</Tag>;
                if (rank === 2) return <Tag color="geekblue" className="text-base px-3 py-1">#2 🥈</Tag>;
                if (rank === 3) return <Tag color="cyan" className="text-base px-3 py-1">#3 🥉</Tag>;
                return <span className="text-gray-500 font-semibold text-lg">#{rank}</span>;
            }
        },
        {
            title: 'Member',
            dataIndex: 'user',
            key: 'user',
            render: (user: any) => (
                <Space>
                    <Avatar src={user?.avatar_url} icon={<UserOutlined />} />
                    <div className="flex flex-col">
                        <Text strong>{user?.name || 'Unknown'}</Text>
                        <Text type="secondary" className="text-xs">{user?.email}</Text>
                    </div>
                </Space>
            )
        },
        {
            title: activeTab === 'bonus' ? 'Total Points' : 'Total Violations',
            key: 'total',
            render: (_: any, record: ReportItem) => (
                <Text strong className="text-lg" type={activeTab === 'bonus' ? 'success' : 'danger'}>
                    {activeTab === 'bonus' ? `+${record.total_points}` : record.total_violations}
                </Text>
            ),
            sorter: (a: ReportItem, b: ReportItem) => {
                return activeTab === 'bonus'
                    ? (a.total_points - b.total_points)
                    : (a.total_violations - b.total_violations);
            },
            defaultSortOrder: 'descend' as const,
        },
        {
            title: 'Record Count',
            dataIndex: 'details_count',
            key: 'count',
            render: (count: number) => <Tag>{count} records</Tag>
        }
    ];

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
                    <DatePicker
                        picker="month"
                        allowClear
                        value={selectedDate}
                        onChange={(date) => setSelectedDate(date)}
                        className="w-full sm:w-40"
                        placeholder="All Time"
                    />
                    <Input
                        prefix={<SearchOutlined className="text-gray-400" />}
                        placeholder="Search member..."
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
                                key: 'bonus',
                                label: (
                                    <Space>
                                        <TrophyOutlined />
                                        <span>Bonus Points</span>
                                    </Space>
                                ),
                                children: screens.md ? <DesktopTableView columns={columns} data={data} loading={loading} /> : <MobileListView data={data} loading={loading} activeTab={activeTab} />
                            },
                            {
                                key: 'violation',
                                label: (
                                    <Space>
                                        <WarningOutlined />
                                        <span>Violations</span>
                                    </Space>
                                ),
                                children: screens.md ? <DesktopTableView columns={columns} data={data} loading={loading} /> : <MobileListView data={data} loading={loading} activeTab={activeTab} />
                            },
                            {
                                key: 'title',
                                label: (
                                    <Space>
                                        <CrownOutlined />
                                        <span>Danh Hiệu</span>
                                    </Space>
                                ),
                                children: (
                                    <Table
                                        columns={[
                                            { title: 'Xếp hạng', key: 'rank', render: (_, __, index) => <RankBadge rank={index + 1} />, width: 80 },
                                            { title: 'Thành viên', key: 'user', render: (item: TitleReportItem) => (
                                                <Space>
                                                    <Avatar src={item.user?.avatar_url} icon={<UserOutlined />} />
                                                    <div className="flex flex-col">
                                                        <span>{item.user?.name}</span>
                                                        <span className="text-xs text-gray-500">{item.user?.email}</span>
                                                    </div>
                                                </Space>
                                            )},
                                            { title: 'Danh hiệu', key: 'title', render: (item: TitleReportItem) => (
                                                item.title ? <TitleBadge title={item.title} /> : <Tag>Chưa có</Tag>
                                            )},
                                            { title: 'Điểm tích lũy', key: 'points', render: (item: TitleReportItem) => <Tag color="green">+{item.total_points}</Tag> },
                                            { title: 'Vi phạm', key: 'violations', render: (item: TitleReportItem) => <Tag color="red">{item.violation_count}</Tag> },
                                        ]}
                                        dataSource={titleData}
                                        rowKey={(record) => record.user?.id}
                                        loading={loading}
                                        pagination={{ pageSize: 10 }}
                                        className="p-4"
                                    />
                                )
                            }
                        ]}
                    />
                </Card>
            </motion.div>

            <div className="mt-12">
                <QuickStats data={data} />
                <TrendChart data={data} />
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
        </>
    );
};

export default ActivityReportPage;
