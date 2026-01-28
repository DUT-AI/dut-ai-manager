import React from 'react';
import { Table, Button, message, Popconfirm, Typography, Card, Tabs } from 'antd';
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

    const items: TabsProps['items'] = [
        {
            key: 'homework',
            label: 'Bài tập',
            children: <Table dataSource={deletedHomeworks || []} columns={homeworkColumns} rowKey="id" loading={homeworkLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
        },
        {
            key: 'bonus',
            label: 'Điểm cộng',
            children: <Table dataSource={deletedBonusPoints || []} columns={bonusColumns} rowKey="id" loading={bonusLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
        },
        {
            key: 'violation',
            label: 'Vi phạm',
            children: <Table dataSource={deletedViolations || []} columns={violationColumns} rowKey="id" loading={violationLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
        },
        {
            key: 'permission',
            label: 'Đơn phép',
            children: <Table dataSource={deletedPermissions || []} columns={permissionColumns} rowKey="id" loading={permissionLoading} pagination={{ pageSize: 10 }} locale={{ emptyText: "Thùng rác trống" }} />
        },
    ];

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <Title level={3} className="!mb-0">Thùng rác</Title>
            </div>

            <Card className="mb-6">
                <Tabs defaultActiveKey="homework" items={items} />
            </Card>
        </div>
    );
};

export default TrashPage;
