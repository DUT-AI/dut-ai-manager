import { useState } from 'react';
import {
    Card,
    List,
    Tag,
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
    FileTextOutlined,
    ClockCircleOutlined,
    EditOutlined,
    DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { PermissionRequestResponse } from '@/types/activity.types';
import { permissionService } from '@/services/api/permission.service';

const { Text } = Typography;

interface Props {
    data: PermissionRequestResponse[];
    onEdit: (item: PermissionRequestResponse) => void;
    onRefresh: () => void;
}

export const PermissionRequestSection = ({ data, onEdit, onRefresh }: Props) => {
    const [detailItem, setDetailItem] = useState<PermissionRequestResponse | null>(null);
    const [drawerOpen, setDrawerOpen] = useState(false);

    const handleDelete = async (id: number) => {
        try {
            await permissionService.deletePermission(id);
            message.success('Đã xóa đơn xin phép');
            onRefresh();
        } catch (error) {
            message.error('Xóa thất bại');
        }
    };

    const openDetail = (item: PermissionRequestResponse) => {
        setDetailItem(item);
        setDrawerOpen(true);
    };

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <FileTextOutlined className="text-blue-500" />
                    <Text strong className="uppercase tracking-wider text-sm">Đơn xin phép</Text>
                    <Badge count={data.length} color="#3b82f6" offset={[2, 0]} />
                </div>
            </div>

            {data.length ? (
                <List
                    dataSource={data}
                    renderItem={(item) => (
                        <Card
                            size="small"
                            className="mb-3 border-l-4 border-l-blue-400 bg-blue-50/20 hover:shadow-sm transition-shadow cursor-pointer"
                            onClick={() => openDetail(item)}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <Tag color="blue">{item.category.toUpperCase()}</Tag>
                                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                                    <Tooltip title="Sửa">
                                        <EditOutlined
                                            className="text-gray-400 hover:text-blue-600 cursor-pointer"
                                            onClick={() => onEdit(item)}
                                        />
                                    </Tooltip>
                                    <Popconfirm title="Xóa đơn này?" onConfirm={() => handleDelete(item.id)}>
                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                    </Popconfirm>
                                </div>
                            </div>
                            <div className="flex items-center text-gray-500 text-xs mb-2">
                                <ClockCircleOutlined className="mr-1" />
                                {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}
                            </div>
                            <Text className="block text-sm text-gray-700 line-clamp-2">{item.note}</Text>
                            <div className="mt-2 pt-2 border-t border-blue-100 flex justify-between items-center text-[10px] text-gray-400">
                                <span>Tạo bởi: {item.creator_name || 'System'}</span>
                                <span>{dayjs(item.created_at).format('DD/MM HH:mm')}</span>
                            </div>
                        </Card>
                    )}
                />
            ) : (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={<span className="text-xs text-gray-400">Không có đơn xin phép</span>}
                />
            )}

            {/* Detail Drawer */}
            <Drawer
                title="Chi tiết đơn xin phép"
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                width={400}
            >
                {detailItem && (
                    <div className="flex flex-col gap-4">
                        <Descriptions column={1} size="small" bordered>
                            <Descriptions.Item label="Loại">
                                <Tag color="blue">{detailItem.category.toUpperCase()}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Ngày">
                                {dayjs(detailItem.date).format('DD/MM/YYYY')}
                            </Descriptions.Item>
                            <Descriptions.Item label="Thời gian">
                                {detailItem.start_time.substring(0, 5)} - {detailItem.end_time.substring(0, 5)}
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider style={{ textAlign: 'left' }} className="!mb-2">Nội dung / Lý do</Divider>
                        <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 text-gray-700 whitespace-pre-wrap">
                            {detailItem.note}
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
