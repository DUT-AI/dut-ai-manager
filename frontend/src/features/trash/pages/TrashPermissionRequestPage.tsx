import React, { useMemo } from 'react';
import { Table, Button, message, Popconfirm, Typography, Tag, Grid } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { UndoOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { permissionService } from '@/features/rbac/services/permission.service';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';
import { useTablePagination } from '@/hooks';
import TrashLayout from '../components/TrashLayout';
import UserDisplay, { type UserDisplayRecord } from '../components/UserDisplay';
import TrashMobileList from '../components/TrashMobileList';

const { Text } = Typography;

export const TrashPermissionRequestPage: React.FC = () => {
    const screens = Grid.useBreakpoint();
    const { page, pageSize, getPaginationProps } = useTablePagination();

    const {
        data: permissionData,
        isLoading: permissionLoading,
        refetch: refetchPermissions
    } = useQuery({
        queryKey: ['deletedPermissions', page, pageSize],
        queryFn: () => permissionService.getPermissions({ deleted: true, page, pageSize }),
    });

    const rawItems = useMemo(() => {
        if (Array.isArray(permissionData?.data)) return permissionData.data;
        if (Array.isArray(permissionData)) return permissionData as unknown as PermissionRequestResponse[];
        return [];
    }, [permissionData]);

    const total = (permissionData as { pagination?: { total?: number } })?.pagination?.total ?? rawItems.length;

    const sortedPermissions = useMemo(() =>
        [...rawItems].sort((a, b) => dayjs(b.updated_at).unix() - dayjs(a.updated_at).unix()),
        [rawItems]
    );

    const handleRestorePermission = async (id: number) => {
        try {
            await permissionService.restorePermission(id);
            message.success('Khôi phục đơn phép thành công');
            refetchPermissions();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const permissionColumns: ColumnsType<PermissionRequestResponse> = [
        {
            title: 'Người gửi',
            key: 'user_name',
            render: (_, record) => <UserDisplay record={record as unknown as UserDisplayRecord} />
        },
        {
            title: 'Loại',
            dataIndex: 'category',
            key: 'category',
            render: (val: string) => <Tag color="blue">{String(val)}</Tag>
        },
        {
            title: 'Lý do/Ghi chú',
            dataIndex: 'note',
            key: 'note'
        },
        {
            title: 'Mục tiêu',
            key: 'target',
            render: (_, record) => {
                const rec = record as { category?: string; homework?: { title?: string }; meeting?: { title?: string } };
                if (rec.category === 'POSTPONE' && rec.homework) {
                    return <Text strong className="text-indigo-600">{rec.homework.title}</Text>;
                }
                if ((rec.category === 'ABSENCE' || rec.category === 'LATE') && rec.meeting) {
                    return <Text strong className="text-purple-600">{rec.meeting.title}</Text>;
                }
                return <Text type="secondary">--</Text>;
            },
        },
        {
            title: 'Hành động',
            key: 'action',
            width: 120,
            render: (_, record) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestorePermission(record.id)}>
                    <Button icon={<UndoOutlined />} type="primary" ghost size="small">
                        Khôi phục
                    </Button>
                </Popconfirm>
            ),
        },
    ];

    return (
        <TrashLayout>
            {!screens.md ? (
                <TrashMobileList
                    dataSource={sortedPermissions as unknown as Record<string, unknown>[]}
                    loading={permissionLoading}
                    columns={['user_name', 'category', 'note']}
                    onRestore={handleRestorePermission}
                />
            ) : (
                <Table
                    dataSource={sortedPermissions}
                    columns={permissionColumns}
                    rowKey="id"
                    loading={permissionLoading}
                    pagination={getPaginationProps(total)}
                    locale={{ emptyText: 'Thùng rác trống' }}
                />
            )}
        </TrashLayout>
    );
};

export default TrashPermissionRequestPage;
