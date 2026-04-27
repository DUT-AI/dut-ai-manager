import React, { useState, useMemo } from 'react';
import {
    Table, Button, Tabs, Space, Popconfirm, Typography, Grid
} from 'antd';
import {
    PlusOutlined, UploadOutlined, EyeOutlined, EditOutlined, DeleteOutlined, ReadOutlined
} from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import type { ColumnsType } from 'antd/es/table';

// Hooks & Types
import { useHomeworkActions } from './homework/hooks/useHomeworkActions';
import type { Homework } from '@/types/homework.types';
import { HomeworkPermission } from '@/types/rbac.types';

// Sub-components
import { SubmissionStatusTag } from './homework/components/SubmissionStatusTag';
import { DeadlineText } from './homework/components/DeadlineText';
import { HomeworkMobileList } from './homework/components/HomeworkMobileList';
import { 
    HomeworkFormModal, 
    SubmitHomeworkModal, 
    SubmissionsDrawer, 
    HomeworkReportTab 
} from '@/components/homework';

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
    const [activeTab, setActiveTab] = useState('1');
    const screens = Grid.useBreakpoint();
    
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
        isFormModalOpen, isSubmitModalOpen, isSubmissionsDrawerOpen, 
        selectedHomework, editingHomework, currentAssignees, assigneesLoading 
    } = state;

    const { 
        myHomeworks, allHomeworks, users, teams, 
        myLoading, allLoading 
    } = data;

    const { 
        handleOpenCreate, handleOpenEdit, handleDelete, 
        handleOpenSubmit, handleViewSubmissions, 
        handleFormSuccess, handleSubmitSuccess 
    } = handlers;

    // Table Columns Definitions
    const myColumns = useMemo<ColumnsType<Homework>>(() => [
        {
            title: 'Tiêu đề',
            dataIndex: 'title',
            key: 'title',
            render: (text: string) => <Text strong className="text-indigo-600">{text}</Text>,
        },
        {
            title: 'Hạn nộp',
            dataIndex: 'deadline',
            key: 'deadline',
            render: (date: string, record: Homework) => (
                <DeadlineText date={date} record={record} />
            ),
        },
        {
            title: 'Tình trạng',
            key: 'status',
            align: 'center',
            render: (_, record: Homework) => (
                <SubmissionStatusTag record={record} />
            )
        },
        {
            title: 'Hành động',
            key: 'action',
            align: 'right',
            render: (_: any, record: Homework) => (
                <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={() => handleOpenSubmit(record)}
                    className="bg-indigo-600 hover:bg-indigo-700"
                >
                    Nộp bài / Xem
                </Button>
            ),
        }
    ], [user?.id, handleOpenSubmit]);

    const adminColumns = useMemo<ColumnsType<Homework>>(() => [
        {
            title: 'Tiêu đề',
            dataIndex: 'title',
            key: 'title',
            width: 200,
        },
        {
            title: 'Mô tả',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
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
            title: 'Thao tác',
            key: 'action',
            width: 280,
            render: (_: any, record: Homework) => (
                <Space>
                    <Button icon={<EyeOutlined />} onClick={() => handleViewSubmissions(record)}>
                        Bài nộp
                    </Button>
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
    ], [hasPermission, handleViewSubmissions, handleOpenEdit, handleDelete]);

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
                columns={activeTab === '1' ? myColumns : adminColumns}
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

            <motion.div variants={itemVariants} className="overflow-x-auto no-scrollbar">
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    type="card"
                    className="homework-tabs"
                    tabBarStyle={{
                        paddingLeft: !screens.md ? '16px' : '0',
                        paddingRight: !screens.md ? '16px' : '0',
                        marginBottom: 0,
                        minWidth: !screens.md ? 'max-content' : '100%'
                    }}
                    items={[
                        {
                            key: '1',
                            label: 'Bài tập của tôi',
                            children: renderListView(myHomeworks, myLoading, "Không có bài tập nào được giao")
                        },
                        ...(isAdminOrLeader() ? [{
                            key: '2',
                            label: 'Quản lý bài tập',
                            children: renderListView(allHomeworks, allLoading)
                        }] : []),
                        {
                            key: '3',
                            label: 'Báo cáo',
                            children: <HomeworkReportTab />
                        }
                    ]}
                />

                {/* Modals & Drawer */}
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

                <SubmitHomeworkModal
                    key={`submit-${selectedHomework?.id ?? 'new'}`}
                    open={isSubmitModalOpen}
                    homework={selectedHomework}
                    onSuccess={handleSubmitSuccess}
                    onCancel={() => dispatch({ type: 'CLOSE_SUBMIT' })}
                />

                <SubmissionsDrawer
                    key={`drawer-${selectedHomework?.id ?? 'new'}`}
                    open={isSubmissionsDrawerOpen}
                    homework={selectedHomework}
                    onClose={() => dispatch({ type: 'CLOSE_SUBMISSIONS' })}
                />
            </motion.div>
        </motion.div>
    );
};

export default HomeworkPage;
