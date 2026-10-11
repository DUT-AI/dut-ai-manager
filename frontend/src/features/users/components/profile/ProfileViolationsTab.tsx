import React, { useMemo, useState } from 'react';
import { Table, Modal, Descriptions } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { useViolations } from '@/features/violations';
import type { ViolationResponse } from '@/features/violations/types/violation.types';
import MonthFilterBar from './MonthFilterBar';

interface ProfileViolationsTabProps {
    userId: number;
    isActive: boolean;
}

export const ProfileViolationsTab: React.FC<ProfileViolationsTabProps> = ({
    userId,
    isActive
}) => {
    // Default to null (no filter by month, showing all)
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [selectedViolation, setSelectedViolation] = useState<ViolationResponse | null>(null);

    const { data: violationsResult, isLoading } = useViolations({
        userId,
        month: selectedDate ? selectedDate.month() + 1 : undefined,
        year: selectedDate ? selectedDate.year() : undefined,
        enabled: isActive && !!userId,
    });

    const violations = violationsResult?.data ?? [];

    const sortedViolations = useMemo(
        () => [...violations].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [violations]
    );

    const columns: ColumnsType<ViolationResponse> = [
        { title: 'Lý do', dataIndex: 'reason', key: 'reason', ellipsis: true },
        { title: 'Ngày vi phạm', dataIndex: 'date', key: 'date', width: 120, render: (d) => dayjs(d).format('DD/MM/YYYY') },
        { title: 'Ngày tạo', dataIndex: 'created_at', key: 'created_at', width: 120, render: (d) => dayjs(d).format('DD/MM/YYYY') }
    ];

    return (
        <>
            <MonthFilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
            <Table
                dataSource={sortedViolations}
                columns={columns}
                rowKey="id"
                loading={isLoading}
                pagination={{ pageSize: 10 }}
                scroll={{ x: 600 }}
                onRow={(record) => ({
                    onClick: () => setSelectedViolation(record),
                    className: 'cursor-pointer hover:bg-gray-50'
                })}
            />

            <Modal
                title={<><WarningOutlined className="text-red-500 mr-2" /> Chi tiết vi phạm</>}
                open={!!selectedViolation}
                onCancel={() => setSelectedViolation(null)}
                footer={null}
            >
                {selectedViolation && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Lý do">{selectedViolation.reason}</Descriptions.Item>
                        <Descriptions.Item label="Ngày vi phạm">
                            {dayjs(selectedViolation.date).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Người tạo">
                            {selectedViolation.creator?.name || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedViolation.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>
        </>
    );
};

export default ProfileViolationsTab;
