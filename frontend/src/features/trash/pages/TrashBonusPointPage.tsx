import React, { useMemo } from 'react';
import { Table, Button, message, Popconfirm, Typography, Grid } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { UndoOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { bonusPointService } from '@/features/activity/services/bonus-point.service';
import type { BonusPointResponse } from '@/features/activity/types/activity.types';
import { useTablePagination } from '@/hooks';
import TrashLayout from '../components/TrashLayout';
import UserDisplay, { type UserDisplayRecord } from '../components/UserDisplay';
import TrashMobileList from '../components/TrashMobileList';

const { Text } = Typography;

export const TrashBonusPointPage: React.FC = () => {
    const screens = Grid.useBreakpoint();
    const { page, pageSize, getPaginationProps } = useTablePagination();

    const {
        data: bonusData,
        isLoading: bonusLoading,
        refetch: refetchBonusPoints
    } = useQuery({
        queryKey: ['deletedBonusPoints', page, pageSize],
        queryFn: () => bonusPointService.getBonusPoints(undefined, undefined, undefined, undefined, true, undefined, undefined, page, pageSize),
    });

    const rawItems = useMemo(() => {
        if (Array.isArray(bonusData?.data)) return bonusData.data;
        if (Array.isArray(bonusData)) return bonusData as unknown as BonusPointResponse[];
        return [];
    }, [bonusData]);

    const total = bonusData?.pagination?.total ?? rawItems.length;

    const sortedBonusPoints = useMemo(() =>
        [...rawItems].sort((a, b) => dayjs(b.updated_at).unix() - dayjs(a.updated_at).unix()),
        [rawItems]
    );

    const handleRestoreBonusPoint = async (id: number) => {
        try {
            await bonusPointService.restoreBonusPoint(id);
            message.success('Khôi phục điểm cộng thành công');
            refetchBonusPoints();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Khôi phục thất bại');
        }
    };

    const bonusColumns: ColumnsType<BonusPointResponse> = [
        {
            title: 'Người nhận',
            key: 'user_name',
            render: (_, record) => <UserDisplay record={record as unknown as UserDisplayRecord} />
        },
        {
            title: 'Điểm',
            dataIndex: 'points',
            key: 'points',
            render: (val: number) => <Text type="success">+{String(val)}</Text>
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
                <Popconfirm title="Khôi phục?" onConfirm={() => handleRestoreBonusPoint(record.id)}>
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
                    dataSource={sortedBonusPoints as unknown as Record<string, unknown>[]}
                    loading={bonusLoading}
                    columns={['user_name', 'points', 'reason']}
                    onRestore={handleRestoreBonusPoint}
                />
            ) : (
                <Table
                    dataSource={sortedBonusPoints}
                    columns={bonusColumns}
                    rowKey="id"
                    loading={bonusLoading}
                    pagination={getPaginationProps(total)}
                    locale={{ emptyText: 'Thùng rác trống' }}
                />
            )}
        </TrashLayout>
    );
};

export default TrashBonusPointPage;
