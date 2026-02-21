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
    Grid, // Added Grid
    List  // Added List
} from 'antd';
import {
    SearchOutlined,
    TrophyOutlined,
    WarningOutlined,
    UserOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/services/api/report.service';
import type { ReportItem, ReportResponse } from '@/types/report.types';
import type { ColumnsType } from 'antd/es/table';
import { useDebounce } from '@/hooks/useDebounce';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid; // Added useBreakpoint hook

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

const ReportPage = () => {
    const [activeTab, setActiveTab] = useState<'bonus' | 'violation'>('bonus');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<ReportItem[]>([]);

    // Filters
    const [selectedDate, setSelectedDate] = useState<dayjs.Dayjs | null>(null);
    const [searchText, setSearchText] = useState('');
    const debouncedSearchText = useDebounce(searchText, 500);

    const fetchData = async () => {
        setLoading(true);
        try {
            const month = selectedDate ? selectedDate.month() + 1 : undefined;
            const year = selectedDate ? selectedDate.year() : undefined;

            let response: ReportResponse;
            if (activeTab === 'bonus') {
                response = await reportService.getBonusPointReport(month, year, debouncedSearchText);
            } else {
                response = await reportService.getViolationReport(month, year, debouncedSearchText);
            }
            setData(response.items || []);
        } catch (error) {
            console.error("Failed to fetch report data", error);
        } finally {
            setLoading(false);
        }
    };

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
        <div className="p-4 md:p-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <Title level={2} className="!m-0">
                        Detailed Reports
                    </Title>
                    <Text type="secondary">View performance statistics and violations leaderboard</Text>
                </div>
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
            </div>

            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-xs"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <Tabs
                    activeKey={activeTab}
                    onChange={(key) => setActiveTab(key as any)}
                    tabBarStyle={{ padding: !screens.md ? '0 12px' : '0 24px', margin: 0 }}
                    size="large"
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
                        }
                    ]}
                />
            </Card>
        </div>
    );
};

export default ReportPage;
