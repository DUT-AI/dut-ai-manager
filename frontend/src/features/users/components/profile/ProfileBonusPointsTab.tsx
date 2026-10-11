import React, { useMemo, useState } from 'react';
import { Table, Tag, Modal, Descriptions } from 'antd';
import { TrophyOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { useBonusPoints } from '@/features/activity';
import { BonusPointType, type BonusPointResponse } from '@/features/activity/types/activity.types';
import MonthFilterBar from './MonthFilterBar';

interface ProfileBonusPointsTabProps {
    userId: number;
    isActive: boolean;
}

export const ProfileBonusPointsTab: React.FC<ProfileBonusPointsTabProps> = ({
    userId,
    isActive
}) => {
    // Default to null (no filter by month, showing all)
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [selectedBonus, setSelectedBonus] = useState<BonusPointResponse | null>(null);

    const { data: bonusPoints = [], isLoading } = useBonusPoints({
        userId,
        month: selectedDate ? selectedDate.month() + 1 : undefined,
        year: selectedDate ? selectedDate.year() : undefined,
        enabled: isActive && !!userId,
    });

    const sortedBonusPoints = useMemo(
        () => [...bonusPoints].sort((a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf()),
        [bonusPoints]
    );

    const columns: ColumnsType<BonusPointResponse> = [
        {
            title: 'Phân loại',
            dataIndex: 'type',
            key: 'type',
            width: 140,
            render: (type, record) => {
                const isClub =
                    type === BonusPointType.CLUB_ACTIVITY ||
                    (!type &&
                        (record.reason?.toLowerCase().includes('hoạt động tại clb') ||
                            record.reason?.toLowerCase().includes('lab')));
                if (isClub) {
                    return <Tag color="blue">Hoạt động CLB</Tag>;
                }
                return <Tag color="purple">Điểm cộng khác</Tag>;
            }
        },
        { title: 'Lý do', dataIndex: 'reason', key: 'reason', ellipsis: true },
        {
            title: 'Điểm',
            dataIndex: 'points',
            key: 'points',
            width: 80,
            render: (val) => <Tag color="green">+{val}</Tag>
        },
        { title: 'Ngày', dataIndex: 'date', key: 'date', width: 120, render: (d) => dayjs(d).format('DD/MM/YYYY') }
    ];

    return (
        <>
            <MonthFilterBar selectedDate={selectedDate} onChange={setSelectedDate} />
            <Table
                dataSource={sortedBonusPoints}
                columns={columns}
                rowKey="id"
                loading={isLoading}
                pagination={{ pageSize: 10 }}
                scroll={{ x: 600 }}
                onRow={(record) => ({
                    onClick: () => setSelectedBonus(record),
                    className: 'cursor-pointer hover:bg-gray-50'
                })}
            />

            <Modal
                title={<><TrophyOutlined className="text-green-500 mr-2" /> Chi tiết điểm cộng</>}
                open={!!selectedBonus}
                onCancel={() => setSelectedBonus(null)}
                footer={null}
            >
                {selectedBonus && (
                    <Descriptions column={1} bordered size="small">
                        <Descriptions.Item label="Phân loại">
                            {selectedBonus.type === BonusPointType.CLUB_ACTIVITY ||
                            (!selectedBonus.type &&
                                (selectedBonus.reason?.toLowerCase().includes('hoạt động tại clb') ||
                                    selectedBonus.reason?.toLowerCase().includes('lab'))) ? (
                                <Tag color="blue">Hoạt động CLB</Tag>
                            ) : (
                                <Tag color="purple">Điểm cộng khác</Tag>
                            )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Lý do">{selectedBonus.reason}</Descriptions.Item>
                        <Descriptions.Item label="Điểm cộng">
                            <Tag color="green">+{selectedBonus.points}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày">
                            {dayjs(selectedBonus.date).format('DD/MM/YYYY')}
                        </Descriptions.Item>
                        <Descriptions.Item label="Ngày tạo">
                            {dayjs(selectedBonus.created_at).format('DD/MM/YYYY HH:mm')}
                        </Descriptions.Item>
                    </Descriptions>
                )}
            </Modal>
        </>
    );
};

export default ProfileBonusPointsTab;
