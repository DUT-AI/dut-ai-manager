import { useState, useEffect } from 'react';
import {
    Card,
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
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/features/academic-report/services/report.service';
import type { ParticipationStats } from '@/features/academic-report/types/report.types';
import { useDebounce } from '@/hooks/useDebounce';
import { motion, type Variants } from 'motion/react';
import { Agentation } from 'agentation';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' },
    },
};

const RankBadge = ({ rank }: { rank: number }) => {
    if (rank === 1) return <Tag color="gold" className="text-base px-2 py-0.5 m-0">#1 🏆</Tag>;
    if (rank === 2) return <Tag color="geekblue" className="text-base px-2 py-0.5 m-0">#2 🥈</Tag>;
    if (rank === 3) return <Tag color="cyan" className="text-base px-2 py-0.5 m-0">#3 🥉</Tag>;
    return <span className="text-gray-500 font-semibold text-lg">#{rank}</span>;
};

const ActivityParticipationPage = () => {
    const screens = useBreakpoint();
    const [loading, setLoading] = useState(false);
    const [participationData, setParticipationData] = useState<ParticipationStats[]>([]);
    const [searchText, setSearchText] = useState('');
    const debouncedSearchText = useDebounce(searchText, 300);

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);

    const fetchData = async () => {
        setLoading(true);
        try {
            const targetMonth = dayjs().month() + 1;
            const targetYear = dayjs().year();
            const data = await reportService.getParticipationLeaderboard(targetMonth, targetYear);
            setParticipationData(data || []);
        } catch (error) {
            console.error('Failed to fetch participation data', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredData = participationData
        .filter((item) => {
            if (!debouncedSearchText) return true;
            const name = item.user?.name?.toLowerCase() || '';
            const email = item.user?.email?.toLowerCase() || '';
            const search = debouncedSearchText.toLowerCase();
            return name.includes(search) || email.includes(search);
        })
        .sort((a, b) => {
            const pointsDiff = (b.total_points || 0) - (a.total_points || 0);
            if (pointsDiff !== 0) return pointsDiff;
            const hoursDiff = (b.total_hours || 0) - (a.total_hours || 0);
            if (hoursDiff !== 0) return hoursDiff;
            const nameA = a.user?.name || '';
            const nameB = b.user?.name || '';
            return nameA.localeCompare(nameB);
        });

    const totalBonusPoints = participationData.reduce(
        (sum, item) => sum + (item.total_bonus_points || 0),
        0
    );
    const totalViolations = participationData.reduce(
        (sum, item) => sum + (item.violation_count || 0),
        0
    );
    const avgBonus =
        participationData.length > 0
            ? (totalBonusPoints / participationData.length).toFixed(2)
            : '0.00';

    return (
        <div className="w-full">
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="w-full"
            >
                <motion.div
                    variants={itemVariants}
                    className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4"
                >
                    <div>
                        <Text type="secondary" className="text-xs md:text-sm">
                            Thống kê chi tiết giờ tham gia, buổi sinh hoạt, điểm cộng và vi phạm trong tháng
                        </Text>
                    </div>
                    <div className="w-full sm:w-auto">
                        <Input
                            prefix={<SearchOutlined className="text-gray-400" />}
                            placeholder="Tìm thành viên..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            allowClear
                            className="w-full sm:w-64"
                        />
                    </div>
                </motion.div>

                <motion.div variants={itemVariants} className="w-full mb-6">
                    <Card
                        className={
                            !screens.md
                                ? 'bg-transparent shadow-none border-none w-full'
                                : 'shadow-xs border-none bg-white/80 backdrop-blur-md w-full'
                        }
                        styles={{ body: { padding: !screens.md ? 0 : undefined } }}
                    >
                        <Table
                            columns={[
                                {
                                    title: 'Xếp hạng',
                                    key: 'rank',
                                    render: (_, __, index) => (
                                        <RankBadge rank={(page - 1) * pageSize + index + 1} />
                                    ),
                                    width: 80,
                                },
                                {
                                    title: 'Thành viên',
                                    key: 'user',
                                    render: (item: ParticipationStats) => (
                                        <Space>
                                            <Avatar
                                                src={item.user?.avatar_url}
                                                icon={<UserOutlined />}
                                            />
                                            <div className="flex flex-col">
                                                <span className="font-medium text-gray-800">
                                                    {item.user?.name || `Thành viên #${item.user_id}`}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {item.user?.email || 'Chưa cập nhật email'}
                                                </span>
                                            </div>
                                        </Space>
                                    ),
                                },
                                {
                                    title: 'Giờ hoạt động',
                                    key: 'hours',
                                    render: (item: ParticipationStats) =>
                                        item.total_sessions === 0 ? (
                                            <Tag>Chưa sinh hoạt</Tag>
                                        ) : (
                                            <Tag color="blue">{item.total_hours}h</Tag>
                                        ),
                                },
                                {
                                    title: 'Buổi tham gia',
                                    key: 'sessions',
                                    render: (item: ParticipationStats) =>
                                        item.total_sessions === 0 ? (
                                            <Tag>Chưa sinh hoạt</Tag>
                                        ) : (
                                            <Tag>{item.total_sessions} buổi</Tag>
                                        ),
                                },
                                {
                                    title: 'Đúng giờ',
                                    key: 'ontime',
                                    render: (item: ParticipationStats) =>
                                        item.total_sessions === 0 ? (
                                            <Tag>Chưa sinh hoạt</Tag>
                                        ) : (
                                            <Tag
                                                color={
                                                    item.on_time_rate >= 0.8
                                                        ? 'success'
                                                        : 'warning'
                                                }
                                            >
                                                {(item.on_time_rate * 100).toFixed(0)}%
                                            </Tag>
                                        ),
                                },
                                {
                                    title: 'Điểm cộng',
                                    key: 'bonus',
                                    render: (item: ParticipationStats) => (
                                        <Tag color="green">+{item.total_bonus_points ?? 0}</Tag>
                                    ),
                                },
                                {
                                    title: 'Vi phạm',
                                    key: 'violations',
                                    render: (item: ParticipationStats) => {
                                        const penalty =
                                            (item.late_count || 0) * 2 +
                                            (item.absent_count || 0) * 5;
                                        return (
                                            <Tag color="red">
                                                {penalty > 0 ? `-${penalty}` : 0}
                                            </Tag>
                                        );
                                    },
                                },
                                {
                                    title: 'Điểm tổng',
                                    key: 'total',
                                    render: (item: ParticipationStats) => (
                                        <Tag
                                            color={
                                                item.total_points > 0
                                                    ? 'success'
                                                    : item.total_points < 0
                                                    ? 'error'
                                                    : 'default'
                                            }
                                            className="font-bold"
                                        >
                                            {item.total_points > 0
                                                ? `+${item.total_points}`
                                                : item.total_points}
                                        </Tag>
                                    ),
                                },
                            ]}
                            dataSource={filteredData}
                            rowKey={(record) => record.user_id}
                            loading={loading}
                            pagination={{
                                pageSize,
                                current: page,
                                pageSizeOptions: ['10', '20', '50', '100'],
                                showSizeChanger: true,
                                showTotal: (total, range) =>
                                    `${range[0]}-${range[1]} của ${total} thành viên`,
                                onChange: (p, ps) => {
                                    setPage(p);
                                    if (ps && ps !== pageSize) setPageSize(ps);
                                },
                            }}
                            className="w-full"
                        />
                    </Card>
                </motion.div>

                <motion.div variants={itemVariants} className="mt-6 mb-8 w-full">
                    <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={8}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Tổng điểm cộng"
                                    value={totalBonusPoints}
                                    valueStyle={{ color: '#22c55e', fontWeight: 'bold' }}
                                    prefix="+"
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={8}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Tổng vi phạm"
                                    value={totalViolations}
                                    valueStyle={{ color: '#ef4444', fontWeight: 'bold' }}
                                />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={8}>
                            <Card className="shadow-sm border-gray-100 rounded-2xl h-full flex flex-col justify-center">
                                <Statistic
                                    title="Điểm cộng TB"
                                    value={avgBonus}
                                    valueStyle={{ color: '#22c55e', fontWeight: 'bold' }}
                                    prefix="+"
                                />
                            </Card>
                        </Col>
                    </Row>
                </motion.div>
            </motion.div>
        </div>
    );
};

export default ActivityParticipationPage;
