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
    WarningOutlined,
    EditOutlined,
    DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ViolationResponse } from '@/types/activity.types';
import { violationService } from '@/services/api/violation.service';

const { Text } = Typography;

interface Props {
    data: ViolationResponse[];
    onEdit: (item: ViolationResponse) => void;
    onRefresh: () => void;
}

export const ViolationSection = ({ data, onEdit, onRefresh }: Props) => {
    const [detailItem, setDetailItem] = useState<ViolationResponse | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(false);

    const handleDelete = async (id: number) => {
        try {
            await violationService.deleteViolation(id);
            message.success('Đã xóa vi phạm');
            onRefresh();
        } catch (error) {
            message.error('Xóa thất bại');
        }
    };

    const openDetail = (item: ViolationResponse) => {
        setDetailItem(item);
        setDrawerOpen(true);
    };

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <WarningOutlined className="text-red-500" />
                    <Text strong className="uppercase tracking-wider text-sm">Vi phạm</Text>
                    <Badge count={data.length} color="#ef4444" offset={[2, 0]} />
                </div>
            </div>

            {data.length ? (
                <List
                    dataSource={data}
                    renderItem={(item) => (
                        <Card
                            size="small"
                            className="mb-3 border-l-4 border-l-red-400 bg-red-50/20 hover:shadow-sm transition-shadow cursor-pointer"
                            onClick={() => openDetail(item)}
                        >
                            <div className="flex justify-between items-center mb-1">
                                <div className="flex items-center gap-2">
                                    <Text strong className="text-red-700">Vi phạm</Text>
                                    <WarningOutlined className="text-red-500 text-xs" />
                                </div>
                                <div role="presentation" className="flex gap-2" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                                    <Tooltip title="Sửa">
                                        <EditOutlined
                                            className="text-gray-400 hover:text-red-600 cursor-pointer"
                                            onClick={() => onEdit(item)}
                                        />
                                    </Tooltip>
                                    <Popconfirm title="Xóa vi phạm này?" onConfirm={() => handleDelete(item.id)}>
                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                    </Popconfirm>
                                </div>
                            </div>
                            <Text className="block text-sm text-gray-600 mb-1">{item.owner?.name || 'Unknown'}</Text>
                            <Text className="block text-sm text-gray-700 line-clamp-2">{item.reason}</Text>
                            <div className="mt-2 pt-2 border-t border-red-100 flex justify-between items-center text-[10px] text-gray-400">
                                <span>Tạo bởi: {item.creator?.name || 'System'}</span>
                                <span>{dayjs(item.created_at).format('DD/MM HH:mm')}</span>
                            </div>
                        </Card>
                    )}
                />
            ) : (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={<span className="text-xs text-gray-400">Tuyệt vời! Không có vi phạm</span>}
                />
            )}

            {/* Detail Drawer */}
            <Drawer
                title="Chi tiết vi phạm"
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                width={400}
            >
                {detailItem && (
                    <div className="flex flex-col gap-4">
                        <Descriptions column={1} size="small" bordered>
                            <Descriptions.Item label="Thành viên">
                                <Text strong>{detailItem.owner?.name || 'Unknown'}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Ngày vi phạm">
                                {dayjs(detailItem.date).format('DD/MM/YYYY HH:mm')}
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider style={{ textAlign: 'left' }} className="!mb-2">Lý do vi phạm</Divider>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-100 text-gray-700 whitespace-pre-wrap">
                            {detailItem.reason}
                        </div>

                        <Divider style={{ textAlign: 'left' }} className="!mb-2">Thông tin hệ thống</Divider>
                        <Descriptions column={1} size="small" className="text-gray-500">
                            <Descriptions.Item label="Tạo bởi">{detailItem.creator?.name || 'N/A'}</Descriptions.Item>
                            <Descriptions.Item label="Ngày ghi nhận">{dayjs(detailItem.created_at).format('DD/MM/YYYY HH:mm:ss')}</Descriptions.Item>
                            {detailItem.updated_at !== detailItem.created_at && (
                                <>
                                    <Descriptions.Item label="Sửa bởi">{detailItem.updater?.name || 'N/A'}</Descriptions.Item>
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
