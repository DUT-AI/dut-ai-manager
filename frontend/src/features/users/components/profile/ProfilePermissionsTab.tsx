import React, { useMemo, useState } from 'react';
import { Table, Tag, Modal, Descriptions } from 'antd';
import { FileProtectOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { usePermissionRequests, CATEGORY_COLORS, CATEGORY_LABELS } from '@/features/rbac';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';
import MonthFilterBar from './MonthFilterBar';

interface ProfilePermissionsTabProps {
    userId: number;
    isActive: boolean;
}

export const ProfilePermissionsTab: React.FC<ProfilePermissionsTabProps> = ({
    userId,
    isActive
}) => {
    // Default to null (no filter by month, showing all)
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [selectedPermission, setSelectedPermission] = useState<PermissionRequestResponse | null>(null);

    const { data: permissionRequests = [], isLoading } = usePermissionRequests({
        userId,
        month: selectedDate ? selectedDate.month() + 1 : undefined,
        year: selectedDate ? selectedDate.year() : undefined,
        enabled: isActive && !!userId,
    });

    const sortedPermissions = useMemo(
        () => [...permissionRequests].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [permissionRequests]
    );

    const columns: ColumnsType<PermissionRequestResponse> = [
        {
            title: 'Loại',
            dataIndex: 'category',
            key: 'category',
            width: 140,
            render: (cat: string) => (
                <Tag color={CATEGORY_COLORS[cat.toLowerCase()] || 'default'} className="rounded-full px-2 font-medium">
                    {CATEGORY_LABELS[cat.toLowerCase()] || cat}
                </Tag>
            ),
        },
        { title: 'Nội dung', dataIndex: 'note', key: 'note', ellipsis: true },
        { title: 'Thời gian', key: 'time', width: 140, render: (_, r) => r.start_time || '--' },
        { title: 'Ngày', dataIndex: 'date', key: 'date', width: 120, render: (d) => dayjs(d).format('DD/MM/YYYY') }
    ];

    return (
        <>
            <MonthFilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
            <Table
                dataSource={sortedPermissions}
                columns={columns}
                rowKey="id"
                loading={isLoading}
                pagination={{ pageSize: 10 }}
                scroll={{ x: 600 }}
                onRow={(record) => ({
                    onClick: () => setSelectedPermission(record),
                    className: 'cursor-pointer hover:bg-gray-50'
                })}
            />

            <Modal
                title={<><FileProtectOutlined className="text-blue-500 mr-2" /> Chi tiết đơn xin phép</>}
                open={!!selectedPermission}
                onCancel={() => setSelectedPermission(null)}
                footer={null}
            >
                {selectedPermission && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Loại">{selectedPermission.category}</Descriptions.Item>
                        <Descriptions.Item label="Nội dung">{selectedPermission.note}</Descriptions.Item>
                        <Descriptions.Item label="Thời gian bắt đầu">
                            {selectedPermission.start_time || '--'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày xin phép">
                            {dayjs(selectedPermission.created_at).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Người tạo">
                            {selectedPermission.creator?.name || selectedPermission.owner?.name || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedPermission.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>
        </>
    );
};

export default ProfilePermissionsTab;
