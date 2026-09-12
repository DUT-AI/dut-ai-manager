import React, { useState, useMemo } from 'react';

import {
    Table, Button, Tabs, Space, Popconfirm, Typography, Grid
} from 'antd';
import {
    PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ReadOutlined, ReloadOutlined
} from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import type { ColumnsType } from 'antd/es/table';

// Hooks & Types
import { useHomeworkActions } from '../hooks/useHomeworkActions';
import { useUnsubmittedReport } from '../hooks/useHomeworks';
import type { Homework } from '@/features/homework/types/homework.types';
import { HomeworkPermission } from '@/features/rbac/types/rbac.types';

// Sub-components
import {
    DeadlineText,
    HomeworkMobileList,
    HomeworkFormModal,
    HomeworkReportTab,
    HomeworkDetailDrawer,
} from '../components';

const { Title, Text } = Typography;

// Animation Variants
const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

export const HomeworkPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState('2');
    const [detailHomework, setDetailHomework] = useState<Homework | null>(null);
    const screens = Grid.useBreakpoint();

    // Report refetch (lifted here for tabBarExtraContent)
    const { isLoading: reportLoading, refetch: refetchReport } = useUnsubmittedReport();

    // Core Logic Hook
    const {
        state,
        dispatch,
        data,
        user,
        hasPermission,
        isAdminOrLeader,
        handlers
    } = useHomeworkActions(activeTab);

    const {
        isFormModalOpen,
        selectedHomework, editingHomework, currentAssignees, assigneesLoading
    } = state;

    const {
        allHomeworks, users, teams,
        allLoading
    } = data;

    const {
        handleOpenCreate, handleOpenEdit, handleDelete,
        handleFormSuccess
    } = handlers;

    // Table Columns Definitions


    const adminColumns = useMemo<ColumnsType<Homework>>(() => [
        {
            title: 'Tiêu đề',
            dataIndex: 'title',
            key: 'title',
            width: 250,
        },
        {
            title: 'Hạn nộp',
            dataIndex: 'deadline',
            key: 'deadline',
            width: 150,
            render: (date: string, record: Homework) => (
                <DeadlineText date={date} record={record} />
            ),
        },
        {
            title: 'Hành động',
            key: 'detail',
            width: 100,
            align: 'center' as const,
            render: (_: any, record: Homework) => (
                <Button
                    icon={<EyeOutlined />}
                    size="small"
                    onClick={() => setDetailHomework(record)}
                    style={{ color: '#6366f1', borderColor: '#6366f1' }}
                >
                    Chi tiết
                </Button>
            ),
        },
        {
            title: 'Thao tác',
            key: 'action',
            width: 120,
            align: 'center' as const,
            render: (_: any, record: Homework) => (
                <Space>
                    {hasPermission(HomeworkPermission.UPDATE) && (
                        <Button icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} />
                    )}
                    {hasPermission(HomeworkPermission.DELETE) && (
                        <Popconfirm
                            title="Xóa bài tập này?"
                            description="Hành động này không thể hoàn tác"
                            onConfirm={() => handleDelete(record.id)}
                            okText="Xóa"
                            cancelText="Hủy"
                            okButtonProps={{ danger: true }}
                        >
                            <Button danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ], [hasPermission, handleOpenEdit, handleDelete, setDetailHomework]);

    const renderListView = (dataSource: Homework[], loading: boolean, emptyText?: string) => {
        if (!screens.md) {
            return (
                <HomeworkMobileList
                    dataSource={dataSource}
                    loading={loading}
                    emptyText={emptyText}
                    activeTab={activeTab}
                    handlers={handlers}
                />
            );
        }
        return (
            <Table
                dataSource={dataSource}
                columns={adminColumns}
                rowKey="id"
                loading={loading}
                locale={{ emptyText }}
            />
        );
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6 bg-white md:rounded-xl shadow-xs min-h-full"
        >
            <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 px-3 md:px-0">
                <Space size="middle">
                    <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-600 shadow-sm">
                        <ReadOutlined className="text-2xl" />
                    </div>
                    <div>
                        <Title level={3} className="text-xl md:text-2xl mt-4 text-indigo-600">Quản lý bài tập</Title>
                        <Text type="secondary" className="text-xs md:text-sm">Giao và nộp bài tập, theo dõi tiến độ</Text>
                    </div>
                </Space>
                {hasPermission(HomeworkPermission.CREATE) && (
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleOpenCreate}
                        className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-700 h-10 font-semibold"
                    >
                        Tạo bài tập mới
                    </Button>
                )}
            </motion.div>

            <motion.div variants={itemVariants}>
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    tabBarExtraContent={activeTab === '3' ? (
                        <Button
                            icon={<ReloadOutlined />}
                            loading={reportLoading}
                            onClick={() => refetchReport()}
                            size="small"
                            className="mr-1"
                        >
                            Làm mới
                        </Button>
                    ) : null}
                    items={[
                        {
                            key: '2',
                            label: 'Quản lý bài tập',
                            children: renderListView(allHomeworks, allLoading)
                        },
                        {
                            key: '3',
                            label: 'Báo cáo',
                            children: <HomeworkReportTab />
                        }
                    ]}
                />

                {/* Modals & Drawers */}
                <HomeworkFormModal
                    key={`form-${editingHomework?.id ?? 'create'}`}
                    open={isFormModalOpen}
                    editingItem={editingHomework}
                    users={users}
                    teams={teams}
                    currentAssignees={currentAssignees}
                    assigneesLoading={assigneesLoading}
                    onSuccess={handleFormSuccess}
                    onCancel={() => dispatch({ type: 'CLOSE_FORM' })}
                />
                <HomeworkDetailDrawer
                    homework={detailHomework}
                    onClose={() => setDetailHomework(null)}
                />
            </motion.div>
        </motion.div>
    );
};

export default HomeworkPage;
