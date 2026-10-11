import React from 'react';
import { Card, List, Typography, Popconfirm, Button } from 'antd';
import { UndoOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import UserDisplay, { type UserDisplayRecord } from './UserDisplay';

const { Text } = Typography;

interface TrashMobileListProps {
    dataSource: Record<string, unknown>[];
    loading: boolean;
    columns: string[];
    onRestore: (id: number) => void;
}

export const TrashMobileList: React.FC<TrashMobileListProps> = ({
    dataSource,
    loading,
    columns,
    onRestore,
}) => (
    <div className="mt-4 px-3">
        <List
            dataSource={dataSource}
            loading={loading}
            split={false}
            locale={{ emptyText: 'Thùng rác trống' }}
            renderItem={(record) => (
                <List.Item className="px-2 mb-4! border-0!">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                    >
                        <div className="flex flex-col gap-2 mb-4">
                            {columns.includes('title') && (
                                <Text strong className="text-base">{String(record.title)}</Text>
                            )}
                            {columns.includes('user_name') && (
                                <div className="mb-2">
                                    <UserDisplay record={record as unknown as UserDisplayRecord} />
                                </div>
                            )}
                            {columns.includes('description') && (
                                <Text type="secondary" className="text-xs italic">{String(record.description)}</Text>
                            )}
                            {columns.includes('reason') && (
                                <div className="bg-gray-50 p-2 rounded text-xs border border-gray-100 italic">
                                    Lý do: {String(record.reason)}
                                </div>
                            )}
                            {columns.includes('points') && (
                                <div className="text-green-600 font-bold">Điểm: +{String(record.points)}</div>
                            )}
                            {columns.includes('category') && (
                                <div className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full inline-block self-start uppercase">
                                    {String(record.category)}
                                </div>
                            )}
                            {columns.includes('note') && (
                                <div className="text-xs text-gray-500 italic">Ghi chú: {String(record.note)}</div>
                            )}
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t border-gray-50">
                            <Text type="secondary" className="text-[10px]">
                                Ngày: {dayjs(String(record.deadline || record.date || record.created_at)).format('DD/MM/YYYY')}
                            </Text>
                            <Popconfirm title="Khôi phục?" onConfirm={() => onRestore(Number(record.id))}>
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

export default TrashMobileList;
