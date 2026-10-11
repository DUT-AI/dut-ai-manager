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
} from 'antd';
import {
    SearchOutlined,
    UserOutlined,
    CrownOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/features/academic-report/services/report.service';
import type { TitleReportItem } from '@/features/academic-report/types/report.types';
import { useDebounce } from '@/hooks/useDebounce';
import { motion, type Variants } from 'motion/react';
import { TitleBadge } from '@/features/users/components/UserTitleBadge';
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

const ActivityTitlesPage = () => {
    const screens = useBreakpoint();
    const [loading, setLoading] = useState(false);
    const [titleData, setTitleData] = useState<TitleReportItem[]>([]);
    const [searchText, setSearchText] = useState('');
    const debouncedSearchText = useDebounce(searchText, 300);

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);

    const fetchData = async () => {
        setLoading(true);
        try {
            const targetMonth = dayjs().month() + 1;
            const targetYear = dayjs().year();
            const titles = await reportService.getTitlesReport(targetMonth, targetYear);
            setTitleData(titles || []);
        } catch (error) {
            console.error('Failed to fetch titles data', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredData = titleData.filter((item) => {
        if (!debouncedSearchText) return true;
        const name = item.user?.name?.toLowerCase() || '';
        const email = item.user?.email?.toLowerCase() || '';
        const search = debouncedSearchText.toLowerCase();
        return name.includes(search) || email.includes(search);
    });

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
                            Bảng vinh danh và xếp hạng danh hiệu thành viên theo tháng
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
                                    render: (item: TitleReportItem) => (
                                        <Space>
                                            <Avatar
                                                src={item.user?.avatar_url}
                                                icon={<UserOutlined />}
                                            />
                                            <div className="flex flex-col">
                                                <span className="font-medium text-gray-800">
                                                    {item.user?.name || `Thành viên #${item.user?.id || '?'}`}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {item.user?.email || 'Chưa cập nhật email'}
                                                </span>
                                            </div>
                                        </Space>
                                    ),
                                },
                                {
                                    title: 'Danh hiệu',
                                    key: 'title',
                                    render: (item: TitleReportItem) =>
                                        item.title ? (
                                            <TitleBadge title={item.title} />
                                        ) : (
                                            <Tag>Chưa có</Tag>
                                        ),
                                },
                                {
                                    title: 'Tổng điểm',
                                    key: 'points',
                                    render: (item: TitleReportItem) => (
                                        <Tag color="green">+{item.total_points}</Tag>
                                    ),
                                },
                                {
                                    title: 'Vi phạm',
                                    key: 'violations',
                                    render: (item: TitleReportItem) => (
                                        <Tag color="red">{item.violation_count}</Tag>
                                    ),
                                },
                            ]}
                            dataSource={filteredData}
                            rowKey={(record) => record.user?.id ?? Math.random()}
                            loading={loading}
                            pagination={{
                                pageSize,
                                current: page,
                                pageSizeOptions: ['10', '20', '50', '100'],
                                showSizeChanger: true,
                                showTotal: (total, range) =>
                                    `${range[0]}-${range[1]} của ${total} danh hiệu`,
                                onChange: (p, ps) => {
                                    setPage(p);
                                    if (ps && ps !== pageSize) setPageSize(ps);
                                },
                            }}
                            className="w-full"
                        />
                    </Card>
                </motion.div>
            </motion.div>
        </div>
    );
};

export default ActivityTitlesPage;
