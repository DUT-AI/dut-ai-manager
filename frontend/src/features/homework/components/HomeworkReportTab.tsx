import React, { useState, useMemo } from 'react';
import { Table, Typography, Drawer, Avatar, Tag, Space, List, Card, Grid, Input, Segmented, Button, Empty, Statistic, Row, Col } from 'antd';
import {
    UserOutlined,
    EyeOutlined,
    SearchOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    TeamOutlined,
    ExportOutlined,
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUnsubmittedReport, useUnsubmittedByUser } from '@/features/homework/hooks/useHomeworks';
import type { HomeworkReportResponse, Homework } from '@/features/homework/types/homework.types';
import type { ColumnsType } from 'antd/es/table';

const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

export const HomeworkReportTab: React.FC = () => {
    const screens = useBreakpoint();
    const { data: reportData, isLoading: reportLoading } = useUnsubmittedReport();
    const [selectedUser, setSelectedUser] = useState<HomeworkReportResponse | null>(null);
    const [searchText, setSearchText] = useState('');
    const [filterType, setFilterType] = useState<'all' | 'unsubmitted' | 'completed'>('all');

    const { data: userHomeworks, isLoading: userHomeworksLoading } = useUnsubmittedByUser(selectedUser?.user_id || null);

    // Summary Statistics
    const stats = useMemo(() => {
        const totalUsers = reportData?.length || 0;
        const usersWithPending = reportData?.filter(u => u.unsubmitted_count > 0).length || 0;
        const fullyCompletedUsers = totalUsers - usersWithPending;
        const totalPendingAssignments = reportData?.reduce((acc, u) => acc + (u.unsubmitted_count || 0), 0) || 0;

        return {
            totalUsers,
            usersWithPending,
            fullyCompletedUsers,
            totalPendingAssignments,
        };
    }, [reportData]);

    // Filtered data based on search and tab filter
    const filteredData = useMemo(() => {
        if (!reportData) return [];
        return reportData.filter(item => {
            const name = item.owner?.name?.toLowerCase() || '';
            const email = item.owner?.email?.toLowerCase() || '';
            const searchLower = searchText.toLowerCase().trim();

            const matchSearch = !searchLower || name.includes(searchLower) || email.includes(searchLower);

            if (!matchSearch) return false;

            if (filterType === 'unsubmitted') {
                return item.unsubmitted_count > 0;
            }
            if (filterType === 'completed') {
                return item.unsubmitted_count === 0;
            }
            return true;
        });
    }, [reportData, searchText, filterType]);

    const columns: ColumnsType<HomeworkReportResponse> = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: HomeworkReportResponse) => (
                <Space size="middle">
                    <Avatar
                        src={record.owner?.avatar_url || undefined}
                        icon={<UserOutlined />}
                        size={40}
                        className="border border-indigo-100 shadow-2xs"
                    />
                    <div>
                        <div className="font-semibold text-gray-900 text-sm">
                            {record.owner?.name || `User #${record.user_id}`}
                        </div>
                        {record.owner?.email && (
                            <div className="text-xs text-gray-400">
                                {record.owner.email}
                            </div>
                        )}
                    </div>
                </Space>
            )
        },
        {
            title: 'Trạng thái',
            key: 'status',
            align: 'center',
            width: 180,
            render: (_: any, record: HomeworkReportResponse) => {
                if (record.unsubmitted_count === 0) {
                    return (
                        <Tag color="success" icon={<CheckCircleOutlined />} className="px-2.5 py-0.5 rounded-full text-xs font-semibold">
                            Hoàn thành tất cả
                        </Tag>
                    );
                }
                return (
                    <Tag color="error" icon={<ExclamationCircleOutlined />} className="px-2.5 py-0.5 rounded-full text-xs font-semibold">
                        Chưa nộp {record.unsubmitted_count} bài
                    </Tag>
                );
            }
        },
        {
            title: 'Số bài chưa nộp',
            dataIndex: 'unsubmitted_count',
            key: 'unsubmitted_count',
            align: 'center',
            width: 160,
            sorter: (a, b) => a.unsubmitted_count - b.unsubmitted_count,
            render: (count: number) => (
                <span className={`font-bold text-sm ${count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {count} bài
                </span>
            )
        },
        {
            title: 'Thao tác',
            key: 'action',
            align: 'center',
            width: 140,
            render: (_: any, record: HomeworkReportResponse) => (
                <Button
                    type="link"
                    size="small"
                    icon={<EyeOutlined />}
                    disabled={record.unsubmitted_count === 0}
                    onClick={() => setSelectedUser(record)}
                    className="font-medium text-indigo-600 hover:text-indigo-800"
                >
                    Xem bài nợ
                </Button>
            )
        }
    ];

    const mobileRenderItem = (item: HomeworkReportResponse) => (
        <List.Item
            className="!px-0 !py-2 !border-0 cursor-pointer"
            onClick={() => item.unsubmitted_count > 0 && setSelectedUser(item)}
        >
            <Card className="w-full shadow-2xs hover:shadow-md transition-shadow rounded-xl border border-gray-100">
                <div className="flex justify-between items-center gap-3">
                    <Space size="middle" className="flex-1 min-w-0">
                        <Avatar
                            src={item.owner?.avatar_url || undefined}
                            icon={<UserOutlined />}
                            size={40}
                        />
                        <div className="min-w-0">
                            <div className="font-semibold text-gray-900 text-sm truncate">
                                {item.owner?.name || `User #${item.user_id}`}
                            </div>
                            <div className="text-xs text-gray-400 truncate">
                                {item.owner?.email || ''}
                            </div>
                        </div>
                    </Space>
                    <div className="shrink-0 text-right">
                        {item.unsubmitted_count === 0 ? (
                            <Tag color="success" className="rounded-full font-semibold text-xs m-0">
                                0 bài nợ
                            </Tag>
                        ) : (
                            <Tag color="error" className="rounded-full font-semibold text-xs m-0">
                                {item.unsubmitted_count} chưa nộp
                            </Tag>
                        )}
                    </div>
                </div>
            </Card>
        </List.Item>
    );

    return (
        <div className="px-3 md:px-0 space-y-5">
            {/* Top KPI Summary Cards */}
            <Row gutter={[16, 16]}>
                <Col xs={12} sm={6}>
                    <Card size="small" className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/50 to-white shadow-2xs">
                        <Statistic
                            title={<span className="text-xs font-semibold text-gray-500 uppercase">Tổng thành viên</span>}
                            value={stats.totalUsers}
                            prefix={<TeamOutlined className="text-indigo-600 text-lg mr-1.5" />}
                            valueStyle={{ color: '#4f46e5', fontWeight: 700 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card size="small" className="rounded-2xl border border-rose-100 bg-gradient-to-br from-rose-50/50 to-white shadow-2xs">
                        <Statistic
                            title={<span className="text-xs font-semibold text-gray-500 uppercase">Còn nợ bài</span>}
                            value={stats.usersWithPending}
                            prefix={<ExclamationCircleOutlined className="text-rose-500 text-lg mr-1.5" />}
                            valueStyle={{ color: '#e11d48', fontWeight: 700 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card size="small" className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/50 to-white shadow-2xs">
                        <Statistic
                            title={<span className="text-xs font-semibold text-gray-500 uppercase">Đã hoàn thành</span>}
                            value={stats.fullyCompletedUsers}
                            prefix={<CheckCircleOutlined className="text-emerald-500 text-lg mr-1.5" />}
                            valueStyle={{ color: '#059669', fontWeight: 700 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card size="small" className="rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50/50 to-white shadow-2xs">
                        <Statistic
                            title={<span className="text-xs font-semibold text-gray-500 uppercase">Tổng số bài nợ</span>}
                            value={stats.totalPendingAssignments}
                            valueStyle={{ color: '#d97706', fontWeight: 700 }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Filter & Search Bar */}
            <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3 bg-gray-50/80 p-3 rounded-xl border border-gray-200/60 mb-4">
                <Input
                    placeholder="Tìm kiếm theo tên hoặc email học viên..."
                    prefix={<SearchOutlined className="text-gray-400" />}
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    allowClear
                    className="w-full sm:w-72 md:w-80 rounded-lg"
                />

                <Segmented
                    value={filterType}
                    onChange={(val) => setFilterType(val as 'all' | 'unsubmitted' | 'completed')}
                    options={[
                        { label: `Tất cả (${reportData?.length || 0})`, value: 'all' },
                        { label: `Còn nợ bài (${stats.usersWithPending})`, value: 'unsubmitted' },
                        { label: `Đã xong (${stats.fullyCompletedUsers})`, value: 'completed' },
                    ]}
                    size="middle"
                    className="shrink-0 font-medium self-start sm:self-auto overflow-x-auto"
                />
            </div>

            {/* Table or Mobile Cards */}
            {!screens.md ? (
                <List
                    dataSource={filteredData}
                    loading={reportLoading}
                    renderItem={mobileRenderItem}
                    split={false}
                    locale={{ emptyText: <Empty description="Không có dữ liệu phù hợp" /> }}
                />
            ) : (
                <Table
                    dataSource={filteredData}
                    columns={columns}
                    rowKey="user_id"
                    loading={reportLoading}
                    pagination={{ pageSize: 15, showTotal: (total) => `Tổng số ${total} học viên` }}
                    className="border border-gray-100 rounded-xl overflow-hidden shadow-2xs"
                />
            )}

            {/* Drawer: Detailed list of unsubmitted homeworks for selected user */}
            <Drawer
                title={
                    <div className="flex items-center gap-3">
                        <Avatar
                            src={selectedUser?.owner?.avatar_url || undefined}
                            icon={<UserOutlined />}
                            size={36}
                        />
                        <div>
                            <div className="font-bold text-base text-gray-900 leading-tight">
                                {selectedUser?.owner?.name || `User #${selectedUser?.user_id}`}
                            </div>
                            <Text type="secondary" className="text-xs">
                                Danh sách bài tập chưa hoàn thành ({selectedUser?.unsubmitted_count} bài)
                            </Text>
                        </div>
                    </div>
                }
                placement="right"
                width={screens.md ? 520 : '100%'}
                onClose={() => setSelectedUser(null)}
                open={!!selectedUser}
            >
                <List
                    loading={userHomeworksLoading}
                    dataSource={userHomeworks || []}
                    locale={{ emptyText: <Empty description="Học viên đã nộp tất cả bài tập 🎉" /> }}
                    renderItem={(hw: Homework) => {
                        const isOverdue = dayjs().isAfter(dayjs(hw.deadline));
                        return (
                            <List.Item className="!px-0 !py-2.5">
                                <Card
                                    size="small"
                                    className={`w-full rounded-xl border shadow-2xs transition-all ${
                                        isOverdue ? 'border-rose-200 bg-rose-50/20' : 'border-gray-200'
                                    }`}
                                >
                                    <div className="flex justify-between items-start gap-2 mb-2">
                                        <Text strong className="text-sm text-gray-900 line-clamp-2">
                                            {hw.title}
                                        </Text>
                                        {isOverdue ? (
                                            <Tag color="red" className="shrink-0 m-0 font-medium text-xs">
                                                Quá hạn
                                            </Tag>
                                        ) : (
                                            <Tag color="blue" className="shrink-0 m-0 font-medium text-xs">
                                                Đang mở
                                            </Tag>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
                                        <CalendarOutlined />
                                        <span>Hạn nộp:</span>
                                        <strong className={isOverdue ? 'text-rose-600' : 'text-gray-700'}>
                                            {dayjs(hw.deadline).format('DD/MM/YYYY HH:mm')}
                                        </strong>
                                    </div>

                                    {hw.link && (
                                        <Button
                                            type="primary"
                                            size="small"
                                            href={hw.link}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            icon={<ExportOutlined />}
                                            className="w-full bg-indigo-600 hover:bg-indigo-700 font-medium rounded-lg"
                                        >
                                            Mở link bài tập trên Quiz
                                        </Button>
                                    )}
                                </Card>
                            </List.Item>
                        );
                    }}
                />
            </Drawer>
        </div>
    );
};
