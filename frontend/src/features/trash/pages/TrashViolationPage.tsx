import React, { useMemo } from 'react';
import { Table, Button, message, Popconfirm, Grid } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { UndoOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { violationService } from '@/features/violations/services/violation.service';
import type { ViolationResponse } from '@/features/violations/types/violation.types';
import { useTablePagination } from '@/hooks';
import TrashLayout from '../components/TrashLayout';
import UserDisplay, { type UserDisplayRecord } from '../components/UserDisplay';
import TrashMobileList from '../components/TrashMobileList';

export const TrashViolationPage: React.FC = () => {
    const screens = Grid.useBreakpoint();
    const { page, pageSize, getPaginationProps } = useTablePagination();

    const {
        data: violationData,
        isLoading: violationLoading,
        refetch: refetchViolations
    } = useQuery({
        queryKey: ['deletedViolations', page, pageSize],
        queryFn: () => violationService.getViolations(page, pageSize, undefined, undefined, undefined, true),
    });

    const rawItems = useMemo(() => {
        if (Array.isArray(violationData?.data)) return violationData.data;
        if (Array.isArray(violationData)) return violationData as unknown as ViolationResponse[];
        return [];
    }, [violationData]);

    const total = violationData?.pagination?.total ?? rawItems.length;

    const sortedViolations = useMemo(() =>
        [...rawItems].sort((a, b) => dayjs(b.updated_at).unix() - dayjs(a.updated_at).unix()),
        [rawItems]
    );

    const handleRestoreViolation = async (id: number) => {
        try {
            await violationService.restoreViolation(id);
            message.success('Khôi phục vi phạm thành công');
            refetchViolations();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const violationColumns: ColumnsType<ViolationResponse> = [
        {
            title: 'Người vi phạm',
            key: 'user_name',
            render: (_, record) => <UserDisplay record={record as unknown as UserDisplayRecord} />
        },
        {
            title: 'Lý do',
            dataIndex: 'reason',
            key: 'reason'
        },
        {
            title: 'Ngày',
            dataIndex: 'date',
            key: 'date',
            render: (date: string) => dayjs(date).format('DD/MM/YYYY')
        },
        {
            title: 'Hành động',
            key: 'action',
            width: 120,
            render: (_, record) => (
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestoreViolation(record.id)}>
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
                    dataSource={sortedViolations as unknown as Record<string, unknown>[]}
                    loading={violationLoading}
                    columns={['user_name', 'reason']}
                    onRestore={handleRestoreViolation}
                />
            ) : (
                <Table
                    dataSource={sortedViolations}
                    columns={violationColumns}
                    rowKey="id"
                    loading={violationLoading}
                    pagination={getPaginationProps(total)}
                    locale={{ emptyText: 'Thùng rác trống' }}
                />
            )}
        </TrashLayout>
    );
};

export default TrashViolationPage;
