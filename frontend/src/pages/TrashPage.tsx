import React from 'react';
import { Table, Button, message, Popconfirm, Typography, Card, Tabs, Grid, List } from 'antd';
import type { TabsProps } from 'antd';
import { UndoOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { homeworkService } from '@/services/api/homework.service';
import { bonusPointService } from '@/services/api/bonus-point.service';
import { violationService } from '@/services/api/violation.service';
import { permissionService } from '@/services/api/permission.service';
import type { Homework } from '@/types/homework.types';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

const TrashMobileList = ({ dataSource, loading, columns, onRestore }: { dataSource: any[], loading: boolean, columns: string[], onRestore: (id: number) => void }) => (
    <div className="mt-4 px-3">
        <List
            dataSource={dataSource}
            loading={loading}
            split={false}
            locale={{ emptyText: "Thùng rác trống" }}
            renderItem={(record) => (
                <List.Item className="px-2 !mb-4 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                    >
                        <div className="flex flex-col gap-2 mb-4">
                            {columns.includes('title') && <Text strong className="text-base">{record.title}</Text>}
                            {columns.includes('user_name') && <Text strong className="text-base">{record.user_name}</Text>}
                            {columns.includes('description') && <Text type="secondary" className="text-xs italic">{record.description}</Text>}
                            {columns.includes('reason') && (
                                <div className="bg-gray-50 p-2 rounded text-xs border border-gray-100 italic">
                                    Lý do: {record.reason}
                                </div>
                            )}
                            {columns.includes('points') && <div className="text-green-600 font-bold">Điểm: +{record.points}</div>}
                            {columns.includes('category') && <div className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full inline-block self-start uppercase">{record.category}</div>}
                            {columns.includes('note') && <div className="text-xs text-gray-500 italic">Ghi chú: {record.note}</div>}
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t border-gray-50">
                            <Text type="secondary" className="text-[10px]">
                                Ngày: {dayjs(record.deadline || record.date).format('DD/MM/YYYY')}
                            </Text>
                            <Popconfirm title="Khôi phục?" onConfirm={() => onRestore(record.id)}>
                                <Button icon={<UndoOutlined />} type="primary" ghost size="small" className="rounded-lg">
                                    Khôi phục
                                </Button>
                            </Popconfirm>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

export const TrashPage: React.FC = () => {
    // Homework Query
    const {
        data: deletedHomeworks = [],
        isLoading: homeworkLoading,
        refetch: refetchHomeworks
    } = useQuery({
        queryKey: ['deletedHomeworks'],
        queryFn: () => homeworkService.getAll(0, 100, true),
    });

    // Bonus Points Query
    const {
        data: deletedBonusPoints = [],
        isLoading: bonusLoading,
        refetch: refetchBonusPoints
    } = useQuery({
        queryKey: ['deletedBonusPoints'],
        queryFn: () => bonusPointService.getBonusPoints(undefined, undefined, undefined, true),
    });

    // Violations Query
    const {
        data: deletedViolations = [],
        isLoading: violationLoading,
        refetch: refetchViolations
    } = useQuery({
        queryKey: ['deletedViolations'],
        // Assuming violation service supports deleted param
        queryFn: () => violationService.getViolations(0, 100, undefined, undefined, undefined, true),
    });

    // Permissions Query
    const {
        data: deletedPermissions = [],
        isLoading: permissionLoading,
        refetch: refetchPermissions
    } = useQuery({
        queryKey: ['deletedPermissions'],
        queryFn: () => permissionService.getPermissions(undefined, undefined, undefined, true),
    });

    // Restore Handlers
    const handleRestoreHomework = async (id: number) => {
        try {
            await homeworkService.restore(id);
            message.success('Khôi phục bài tập thành công');
            refetchHomeworks();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const handleRestoreBonusPoint = async (id: number) => {
        try {
            await bonusPointService.restoreBonusPoint(id);
            message.success('Khôi phục điểm cộng thành công');
            refetchBonusPoints();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const handleRestoreViolation = async (id: number) => {
        try {
            await violationService.restoreViolation(id);
            message.success('Khôi phục vi phạm thành công');
            refetchViolations();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const handleRestorePermission = async (id: number) => {
        try {
            await permissionService.restorePermission(id);
            message.success('Khôi phục đơn phép thành công');
            refetchPermissions();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    // Columns
    const homeworkColumns: ColumnsType<Homework> = [
        { title: 'Tiêu đề', dataIndex: 'title', key: 'title', render: (text) => <Text strong>{text}</Text> },
        { title: 'Mô tả', dataIndex: 'description', key: 'description', ellipsis: true },
        { title: 'Hạn nộp', dataIndex: 'deadline', key: 'deadline', render: (date) => dayjs(date).format('DD/MM/YYYY HH:mm') },
        {
            title: 'Hành động', key: 'action', width: 120,
            render: (_: any, record: Homework) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestoreHomework(record.id)}>
                    <Button icon={<UndoOutlined />} type="primary" ghost size="small">Khôi phục</Button>
                </Popconfirm>
            ),
        },
    ];

    const bonusColumns: ColumnsType<any> = [
        { title: 'Người nhận', dataIndex: 'user_name', key: 'user_name' },
        { title: 'Điểm', dataIndex: 'points', key: 'points', render: (val) => <Text type="success">+{val}</Text> },
        { title: 'Lý do', dataIndex: 'reason', key: 'reason' },
        { title: 'Ngày', dataIndex: 'date', key: 'date', render: (date) => dayjs(date).format('DD/MM/YYYY') },
        {
            title: 'Hành động', key: 'action', width: 120,
            render: (_: any, record: any) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestoreBonusPoint(record.id)}>
                    <Button icon={<UndoOutlined />} type="primary" ghost size="small">Khôi phục</Button>
                </Popconfirm>
            ),
        },
    ];

    const violationColumns: ColumnsType<any> = [
        { title: 'Người vi phạm', dataIndex: 'user_name', key: 'user_name' },
        { title: 'Lý do', dataIndex: 'reason', key: 'reason' },
        { title: 'Ngày', dataIndex: 'date', key: 'date', render: (date) => dayjs(date).format('DD/MM/YYYY') },
        {
            title: 'Hành động', key: 'action', width: 120,
            render: (_: any, record: any) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestoreViolation(record.id)}>
                    <Button icon={<UndoOutlined />} type="primary" ghost size="small">Khôi phục</Button>
                </Popconfirm>
            ),
        },
    ];

    const permissionColumns: ColumnsType<any> = [
        { title: 'Người gửi', dataIndex: 'user_name', key: 'user_name' }, // Check if user_name is available in response
        { title: 'Loại', dataIndex: 'category', key: 'category' },
        { title: 'Lý do/Ghi chú', dataIndex: 'note', key: 'note' },
        { title: 'Ngày', dataIndex: 'date', key: 'date', render: (date) => dayjs(date).format('DD/MM/YYYY') },
        {
            title: 'Hành động', key: 'action', width: 120,
            render: (_: any, record: any) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestorePermission(record.id)}>
                    <Button icon={<UndoOutlined />} type="primary" ghost size="small">Khôi phục</Button>
                </Popconfirm>
            ),
        },
    ];

    const screens = Grid.useBreakpoint();

    const items: TabsProps['items'] = [
        {
            key: 'homework',
            label: 'Bài tập',
            children: !screens.md ? (
                <TrashMobileList
                    dataSource={deletedHomeworks || []}
                    loading={homeworkLoading}
                    columns={['title', 'description']}
                    onRestore={handleRestoreHomework}
                />
            ) : (
                <Table dataSource={deletedHomeworks || []} columns={homeworkColumns} rowKey="id" loading={homeworkLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
            )
        },
        {
            key: 'bonus',
            label: 'Điểm cộng',
            children: !screens.md ? (
                <TrashMobileList
                    dataSource={deletedBonusPoints || []}
                    loading={bonusLoading}
                    columns={['user_name', 'points', 'reason']}
                    onRestore={handleRestoreBonusPoint}
                />
            ) : (
                <Table dataSource={deletedBonusPoints || []} columns={bonusColumns} rowKey="id" loading={bonusLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
            )
        },
        {
            key: 'violation',
            label: 'Vi phạm',
            children: !screens.md ? (
                <TrashMobileList
                    dataSource={deletedViolations || []}
                    loading={violationLoading}
                    columns={['user_name', 'reason']}
                    onRestore={handleRestoreViolation}
                />
            ) : (
                <Table dataSource={deletedViolations || []} columns={violationColumns} rowKey="id" loading={violationLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
            )
        },
        {
            key: 'permission',
            label: 'Đơn phép',
            children: !screens.md ? (
                <TrashMobileList
                    dataSource={deletedPermissions || []}
                    loading={permissionLoading}
                    columns={['user_name', 'category', 'note']}
                    onRestore={handleRestorePermission}
                />
            ) : (
                <Table dataSource={deletedPermissions || []} columns={permissionColumns} rowKey="id" loading={permissionLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
            )
        },
    ];

    return (
        <div className="p-4 md:p-6 bg-[#f8fafc] min-h-full">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 px-3 md:px-0">
                <div>
                    <Title level={3} className="!m-0 text-xl md:text-2xl text-gray-800 mt-4 leading-relaxed">Thùng rác</Title>
                    <Text type="secondary" className="text-xs md:text-sm">Quản lý và khôi phục các dữ liệu đã xóa</Text>
                </div>
            </div>

            <Card className={!screens.md ? "bg-transparent shadow-none border-none p-0" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <div className="overflow-x-auto no-scrollbar">
                    <Tabs
                        defaultActiveKey="homework"
                        items={items}
                        className="trash-tabs"
                        tabBarStyle={{
                            paddingLeft: !screens.md ? '16px' : '24px',
                            paddingRight: !screens.md ? '16px' : '24px',
                            margin: 0,
                            minWidth: !screens.md ? 'max-content' : '100%',
                            borderBottom: '1px solid #f0f0f0'
                        }}
                    />
                </div>
            </Card>
        </div>
    );
};

