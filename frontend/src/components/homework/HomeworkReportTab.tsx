import React, { useState } from 'react';
import { Table, Typography, Drawer, Avatar, Tag, Space, List, Card, Grid } from 'antd';
import { UserOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUnsubmittedReport, useUnsubmittedByUser } from '@/hooks/useHomeworks';
import type { HomeworkReportResponse, Homework } from '@/types/homework.types';
import type { ColumnsType } from 'antd/es/table';

const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

export const HomeworkReportTab: React.FC = () => {
    const screens = useBreakpoint();
    const { data: reportData, isLoading: reportLoading } = useUnsubmittedReport();
    const [selectedUser, setSelectedUser] = useState<HomeworkReportResponse | null>(null);

    const { data: userHomeworks, isLoading: userHomeworksLoading } = useUnsubmittedByUser(selectedUser?.user_id || null);

    const columns: ColumnsType<HomeworkReportResponse> = [
        {
            title: 'Người dùng',
            key: 'user',
            render: (_: any, record: HomeworkReportResponse) => (
                <Space>
                    <Avatar src={record.user_avatar} icon={<UserOutlined />} />
                    <Text strong>{record.user_name}</Text>
                </Space>
            )
        },
        {
            title: 'Số bài tập chưa nộp',
            dataIndex: 'unsubmitted_count',
            key: 'unsubmitted_count',
            align: 'center',
            render: (count: number) => (
                <Tag color={count > 0 ? 'red' : 'green'}>
                    {count}
                </Tag>
            )
        },
        {
            title: 'Hành động',
            key: 'action',
            align: 'center',
            render: (_: any, record: HomeworkReportResponse) => (
                <div onClick={() => setSelectedUser(record)} className="text-indigo-600 hover:text-indigo-800 cursor-pointer flex items-center justify-center gap-1">
                    <EyeOutlined /> Chi tiết
                </div>
            )
        }
    ];

    const mobileRenderItem = (item: HomeworkReportResponse) => (
        <List.Item className="px-2 !mb-4 !border-0 cursor-pointer" onClick={() => setSelectedUser(item)}>
            <Card className="w-full shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-center">
                    <Space>
                        <Avatar src={item.user_avatar} icon={<UserOutlined />} />
                        <Text strong>{item.user_name}</Text>
                    </Space>
                    <Tag color={item.unsubmitted_count > 0 ? 'red' : 'green'}>{item.unsubmitted_count} chưa nộp</Tag>
                </div>
            </Card>
        </List.Item>
    );

    return (
        <div className="mt-4 px-3 md:px-0">
            {!screens.md ? (
                <List
                    dataSource={reportData || []}
                    loading={reportLoading}
                    renderItem={mobileRenderItem}
                    split={false}
                />
            ) : (
                <Table
                    dataSource={reportData || []}
                    columns={columns}
                    rowKey="user_id"
                    loading={reportLoading}
                    pagination={{ pageSize: 20 }}
                />
            )}

            <Drawer
                title={`Chi tiết bài chưa nộp: ${selectedUser?.user_name || ''}`}
                placement="right"
                width={screens.md ? 500 : '100%'}
                onClose={() => setSelectedUser(null)}
                open={!!selectedUser}
            >
                <List
                    loading={userHomeworksLoading}
                    dataSource={userHomeworks || []}
                    locale={{ emptyText: 'Không có bài tập nào chưa nộp' }}
                    renderItem={(hw: Homework) => (
                        <List.Item>
                            <Card className="w-full" size="small">
                                <div className="flex justify-between mb-2">
                                    <Text strong>{hw.title}</Text>
                                    {dayjs().isAfter(dayjs(hw.deadline)) && (
                                        <Tag color="red">Quá hạn</Tag>
                                    )}
                                </div>
                                <Text type="secondary" className="block mb-2 text-sm">{hw.description}</Text>
                                <div className="text-xs text-gray-500">
                                    Hạn nộp: <Text className={dayjs().isAfter(dayjs(hw.deadline)) ? 'text-red-500' : ''}>
                                        {dayjs(hw.deadline).format('DD/MM/YYYY HH:mm')}
                                    </Text>
                                </div>
                            </Card>
                        </List.Item>
                    )}
                />
            </Drawer>
        </div>
    );
};
