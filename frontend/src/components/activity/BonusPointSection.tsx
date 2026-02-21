import { useState } from 'react';
import {
    Card,
    List,
    Badge,
    Typography,
    Empty,
    Tooltip,
    Popconfirm,
    Drawer,
    Descriptions,
    Divider,
    message
} from 'antd';
import {
    PlusCircleOutlined,
    CheckCircleOutlined,
    EditOutlined,
    DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { BonusPointResponse } from '@/types/activity.types';
import { bonusPointService } from '@/services/api/bonus-point.service';

const { Text } = Typography;

interface Props {
    data: BonusPointResponse[];
    onEdit: (item: BonusPointResponse) => void;
    onRefresh: () => void;
}

export const BonusPointSection = ({ data, onEdit, onRefresh }: Props) => {
    const [detailItem, setDetailItem] = useState<BonusPointResponse | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(false);

    const handleDelete = async (id: number) => {
        try {
            await bonusPointService.deleteBonusPoint(id);
            message.success('Đã xóa điểm cộng');
            onRefresh();
        } catch (error) {
            message.error('Xóa thất bại');
        }
    };

    const openDetail = (item: BonusPointResponse) => {
        setDetailItem(item);
        setDrawerOpen(true);
    };

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <PlusCircleOutlined className="text-green-500" />
                    <Text strong className="uppercase tracking-wider text-sm">Điểm cộng</Text>
                    <Badge count={data.length} color="#10b981" offset={[2, 0]} />
                </div>
            </div>

            {data.length ? (
                <List
                    dataSource={data}
                    renderItem={(item) => (
                        <Card
                            size="small"
                            className="mb-3 border-l-4 border-l-green-400 bg-green-50/20 hover:shadow-sm transition-shadow cursor-pointer"
                            onClick={() => openDetail(item)}
                        >
                            <div className="flex justify-between items-center mb-1">
                                <div className="flex items-center gap-2">
                                    <Text strong className="text-green-700">+{item.points} Điểm</Text>
                                    <CheckCircleOutlined className="text-green-500 text-xs" />
                                </div>
                                <div role="presentation" className="flex gap-2" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                                    <Tooltip title="Sửa">
                                        <EditOutlined
                                            className="text-gray-400 hover:text-green-600 cursor-pointer"
                                            onClick={() => onEdit(item)}
                                        />
                                    </Tooltip>
                                    <Popconfirm title="Xóa điểm cộng này?" onConfirm={() => handleDelete(item.id)}>
                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                    </Popconfirm>
                                </div>
                            </div>
                            <Text className="block text-sm text-gray-600 mb-1">{item.user_name || 'Unknown'}</Text>
                            <Text className="block text-sm text-gray-700 line-clamp-2">{item.reason}</Text>
                            <div className="mt-2 pt-2 border-t border-green-100 flex justify-between items-center text-[10px] text-gray-400">
                                <span>Tạo bởi: {item.creator_name || 'System'}</span>
                                <span>{dayjs(item.created_at).format('DD/MM HH:mm')}</span>
                            </div>
                        </Card>
                    )}
                />
            ) : (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={<span className="text-xs text-gray-400">Chưa có điểm cộng</span>}
                />
            )}

            {/* Detail Drawer */}
            <Drawer
                title="Chi tiết điểm cộng"
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                width={400}
            >
                {detailItem && (
                    <div className="flex flex-col gap-4">
                        <Descriptions column={1} size="small" bordered>
                            <Descriptions.Item label="Thành viên">
                                <Text strong>{detailItem.user_name || 'Unknown'}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Điểm số">
                                <Text strong className="text-green-600">+{detailItem.points}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Ngày">
                                {dayjs(detailItem.date).format('DD/MM/YYYY HH:mm')}
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider style={{ textAlign: 'left' }} className="!mb-2">Lý do</Divider>
                        <div className="bg-green-50 p-4 rounded-lg border border-green-100 text-gray-700 whitespace-pre-wrap">
                            {detailItem.reason}
                        </div>

                        <Divider style={{ textAlign: 'left' }} className="!mb-2">Thông tin hệ thống</Divider>
                        <Descriptions column={1} size="small" className="text-gray-500">
                            <Descriptions.Item label="Tạo bởi">{detailItem.creator_name || 'N/A'}</Descriptions.Item>
                            <Descriptions.Item label="Ngày tạo">{dayjs(detailItem.created_at).format('DD/MM/YYYY HH:mm:ss')}</Descriptions.Item>
                            {detailItem.updated_at !== detailItem.created_at && (
                                <>
                                    <Descriptions.Item label="Sửa bởi">{detailItem.updater_name || 'N/A'}</Descriptions.Item>
                                    <Descriptions.Item label="Ngày sửa">{dayjs(detailItem.updated_at).format('DD/MM/YYYY HH:mm:ss')}</Descriptions.Item>
                                </>
                            )}
                        </Descriptions>
                    </div>
                )}
            </Drawer>
        </section>
    );
};
