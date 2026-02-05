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
    Row,
    Col
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
import { useDebounce } from '@/hooks/useDebounce';

const { Title, Text } = Typography;

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

    return (
        <div className="p-6">
            <Row gutter={[16, 16]} align="middle" className="mb-6">
                <Col flex="auto">
                    <Title level={2} className="!m-0">
                        Detailed Reports
                    </Title>
                    <Text type="secondary">View performance statistics and violations leaderboard</Text>
                </Col>
                <Col>
                    <Space>
                        <DatePicker
                            picker="month"
                            allowClear
                            value={selectedDate}
                            onChange={(date) => setSelectedDate(date)}
                            className="w-40"
                            placeholder="All Time"
                        />
                        <Input
                            prefix={<SearchOutlined className="text-gray-400" />}
                            placeholder="Search member..."
                            value={searchText}
                            onChange={e => setSearchText(e.target.value)}
                            allowClear
                            className="w-64"
                        />
                    </Space>
                </Col>
            </Row>

            <Card className="shadow-xs" styles={{ body: { padding: 0 } }}>
                <Tabs
                    activeKey={activeTab}
                    onChange={(key) => setActiveTab(key as any)}
                    tabBarStyle={{ padding: '0 24px', margin: 0 }}
                    size="large"
                    items={[
                        {
                            key: 'bonus',
                            label: (
                                <Space>
                                    <TrophyOutlined />
                                    <span>Bonus Points Leaderboard</span>
                                </Space>
                            ),
                            children: (
                                <Table
                                    columns={columns}
                                    dataSource={data}
                                    rowKey={(record) => record.user?.id || Math.random()}
                                    loading={loading}
                                    pagination={{ pageSize: 10 }}
                                    className="p-4"
                                />
                            )
                        },
                        {
                            key: 'violation',
                            label: (
                                <Space>
                                    <WarningOutlined />
                                    <span>Violations Statistics</span>
                                </Space>
                            ),
                            children: (
                                <Table
                                    columns={columns}
                                    dataSource={data}
                                    rowKey={(record) => record.user?.id || Math.random()}
                                    loading={loading}
                                    pagination={{ pageSize: 10 }}
                                    className="p-4"
                                />
                            )
                        }
                    ]}
                />
            </Card>
        </div>
    );
};

export default ReportPage;
