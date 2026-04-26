import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { reportService } from "../services/api/report.service";
import { Card, Col, DatePicker, Empty, List, Row, Spin, Tag, Typography } from "antd";
import dayjs from "dayjs";
import {
    ClockCircleOutlined,
    ExclamationCircleOutlined,
    StarOutlined,
    FileTextOutlined,
    TeamOutlined
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";

const { Title, Text } = Typography;

const HomePage = () => {
    const { user } = useAuth();
    const [date, setDate] = useState(() => dayjs());

    const { data, isLoading } = useQuery({
        queryKey: ['dashboard-overview', date.month(), date.year()],
        queryFn: () => reportService.getDashboardOverview(date.month() + 1, date.year()),
    });

    const stats = [
        {
            title: "Điểm cộng",
            value: data?.bonus_points.length || 0,
            icon: <StarOutlined className="text-yellow-500 text-2xl" />,
            color: "bg-yellow-50",
        },
        {
            title: "Vi phạm",
            value: data?.violations.length || 0,
            icon: <ExclamationCircleOutlined className="text-red-500 text-2xl" />,
            color: "bg-red-50",
        },
        {
            title: "Đơn phép",
            value: data?.permission_requests.length || 0,
            icon: <FileTextOutlined className="text-blue-500 text-2xl" />,
            color: "bg-blue-50",
        },
        {
            title: "Bài tập chưa nộp",
            value: data?.unsubmitted_homeworks.length || 0,
            icon: <ClockCircleOutlined className="text-orange-500 text-2xl" />,
            color: "bg-orange-50",
        },
    ];

    return (
        <div className="max-w-7xl mx-auto py-6 px-4 md:px-6 md:py-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
                <div>
                    <Title level={3} className="!mb-1">
                        Xin chào, <span className="text-indigo-600">{user?.name}</span> 👋
                    </Title>
                    <Text type="secondary">Tổng quan hoạt động của bạn trong tháng này</Text>
                </div>
                <DatePicker
                    picker="month"
                    value={date}
                    onChange={(val) => val && setDate(val)}
                    allowClear={false}
                    className="w-full md:w-40"
                />
            </div>

            {isLoading ? (
                <div className="flex justify-center py-20">
                    <Spin size="large" />
                </div>
            ) : (
                <>
                    {/* Stats Cards */}
                    <Row gutter={[16, 16]} className="mb-8">
                        {stats.map((stat) => (
                            <Col xs={24} sm={12} md={6} key={stat.title}>
                                <Card variant="borderless" className="shadow-sm hover:shadow-md transition-shadow">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-xl ${stat.color}`}>
                                            {stat.icon}
                                        </div>
                                        <div>
                                            <Text type="secondary" className="block text-xs uppercase font-semibold mb-1">
                                                {stat.title}
                                            </Text>
                                            <span className="text-2xl font-bold block leading-none">
                                                {stat.value}
                                            </span>
                                        </div>
                                    </div>
                                </Card>
                            </Col>
                        ))}
                    </Row>

                    <Row gutter={[24, 24]}>
                        {/* Left Column */}
                        <Col xs={24} lg={16}>
                            <div className="flex flex-col gap-6">
                                {/* Unsubmitted Homework */}
                                <Card
                                    title={<span className="font-bold flex items-center gap-2"><ClockCircleOutlined className="text-orange-500" /> Bài tập cần làm</span>}
                                    variant="borderless"
                                    className="shadow-sm"
                                >
                                    <List
                                        dataSource={data?.unsubmitted_homeworks}
                                        locale={{ emptyText: <Empty description="Không có bài tập nào" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
                                        renderItem={(item) => (
                                            <List.Item>
                                                <List.Item.Meta
                                                    avatar={<div className="bg-orange-50 p-2 rounded-lg text-orange-500 font-bold">{dayjs(item.deadline).format("DD/MM")}</div>}
                                                    title={item.title}
                                                    description={
                                                        <div className="flex items-center gap-2 text-xs">
                                                            <span className="text-gray-500">Hạn nộp: {dayjs(item.deadline).format("HH:mm DD/MM/YYYY")}</span>
                                                            {(() => {
                                                                const status = item.submissions?.[0]?.status;
                                                                if (!status || status === 'chưa nộp') {
                                                                    if (dayjs().isAfter(dayjs(item.deadline))) return <Tag color="red" className="m-0 border-0">Quá hạn</Tag>;
                                                                    return <Tag color="orange" className="m-0 border-0">Chưa nộp</Tag>;
                                                                }
                                                                if (status === 'đã nộp') return <Tag color="blue" className="m-0 border-0">Đã nộp</Tag>;
                                                                if (status === 'leader đã check') return <Tag color="cyan" className="m-0 border-0">Đã kiểm tra</Tag>;
                                                                if (status === 'finish') return <Tag color="green" className="m-0 border-0">Hoàn thành</Tag>;
                                                                return <Tag color="default" className="m-0 border-0">{status}</Tag>;
                                                            })()}
                                                        </div>
                                                    }
                                                />
                                            </List.Item>
                                        )}
                                    />
                                </Card>

                                {/* Meetings */}
                                <Card
                                    title={<span className="font-bold flex items-center gap-2"><TeamOutlined className="text-indigo-500" /> Lịch họp tháng này</span>}
                                    variant="borderless"
                                    className="shadow-sm"
                                >
                                    <List
                                        dataSource={data?.meetings}
                                        locale={{ emptyText: <Empty description="Không có lịch họp nào" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
                                        renderItem={(item) => (
                                            <List.Item>
                                                <List.Item.Meta
                                                    avatar={<div className="bg-indigo-50 p-2 rounded-lg text-indigo-500 font-bold">{dayjs(item.start_time).format("DD")}</div>}
                                                    title={item.title}
                                                    description={`${dayjs(item.start_time).format("HH:mm")} - ${dayjs(item.end_time).format("HH:mm")}`}
                                                />
                                            </List.Item>
                                        )}
                                    />
                                </Card>
                            </div>
                        </Col>

                        {/* Right Column */}
                        <Col xs={24} lg={8}>
                            <div className="flex flex-col gap-6">
                                {/* Recent Activity / Violations / Bonus */}
                                <Card
                                    title={<span className="font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500"></div> Vi phạm gần đây</span>}
                                    variant="borderless"
                                    className="shadow-sm"
                                    styles={{ body: { padding: '12px 24px' } }}
                                >
                                    <List
                                        dataSource={data?.violations.slice(0, 5)}
                                        size="small"
                                        locale={{ emptyText: <Empty description="Chưa có vi phạm nào" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
                                        renderItem={(item) => (
                                            <List.Item className="!px-0">
                                                <div className="w-full">
                                                    <div className="flex justify-between mb-1">
                                                        <Text strong className="text-xs">{dayjs(item.date).format("DD/MM/YYYY")}</Text>
                                                        <Tag color="red" className="mr-0 rounded-full text-[10px] px-2">Vi phạm</Tag>
                                                    </div>
                                                    <Text type="secondary" className="text-xs block">{item.reason}</Text>
                                                </div>
                                            </List.Item>
                                        )}
                                    />
                                </Card>

                                <Card
                                    title={<span className="font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-yellow-500"></div> Điểm cộng gần đây</span>}
                                    variant="borderless"
                                    className="shadow-sm"
                                    styles={{ body: { padding: '12px 24px' } }}
                                >
                                    <List
                                        dataSource={data?.bonus_points.slice(0, 5)}
                                        size="small"
                                        locale={{ emptyText: <Empty description="Chưa có điểm cộng nào" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
                                        renderItem={(item) => (
                                            <List.Item className="!px-0">
                                                <div className="w-full">
                                                    <div className="flex justify-between mb-1">
                                                        <Text strong className="text-xs">{dayjs(item.date).format("DD/MM/YYYY")}</Text>
                                                        <Tag color="gold" className="mr-0 rounded-full text-[10px] px-2">+{item.points}</Tag>
                                                    </div>
                                                    <Text type="secondary" className="text-xs block">{item.reason}</Text>
                                                </div>
                                            </List.Item>
                                        )}
                                    />
                                </Card>
                            </div>
                        </Col>
                    </Row>
                </>
            )
            }
        </div >
    );
};

export default HomePage;
