import React from 'react';
import { Table, Space, Typography, Tag, Button, Popconfirm } from 'antd';
import { CalendarOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { TablePaginationConfig } from 'antd';
import type { MeetingResponse } from '@/features/meeting/types/meeting.types';

const { Text } = Typography;

export interface MeetingTableProps {
  meetings: MeetingResponse[];
  isLoading: boolean;
  paginationProps?: TablePaginationConfig;
  canUpdate?: boolean;
  canDelete?: boolean;
  onView?: (meeting: MeetingResponse) => void;
  onEdit?: (meeting: MeetingResponse) => void;
  onDelete?: (id: number) => void;
}

export const MeetingTable: React.FC<MeetingTableProps> = ({
  meetings,
  isLoading,
  paginationProps,
  canUpdate = false,
  canDelete = false,
  onView,
  onEdit,
  onDelete,
}) => {
  const columns = [
    {
      title: 'Tiêu đề cuộc họp',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: MeetingResponse) => (
        <div className="flex flex-col">
          <Text strong className="text-gray-900 cursor-pointer hover:text-indigo-600" onClick={() => onView?.(record)}>
            {title}
          </Text>
          {record.content && (
            <Text type="secondary" className="text-xs truncate max-w-xs">
              {record.content}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: 'Thời gian',
      key: 'time',
      render: (_: unknown, record: MeetingResponse) => (
        <Space direction="vertical" size={2}>
          <div className="flex items-center text-xs text-gray-600">
            <CalendarOutlined className="mr-1 text-indigo-500" />
            <span>{dayjs(record.start_time).format('DD/MM/YYYY HH:mm')} - {dayjs(record.end_time).format('HH:mm')}</span>
          </div>
        </Space>
      ),
    },
    {
      title: 'Điểm danh',
      key: 'require_check_in',
      render: (_: unknown, record: MeetingResponse) => (
        <Tag color={record.require_check_in ? 'blue' : 'default'}>
          {record.require_check_in ? 'Bắt buộc' : 'Không bắt buộc'}
        </Tag>
      ),
    },
    {
      title: 'Đánh giá',
      key: 'enable_evaluation',
      render: (_: unknown, record: MeetingResponse) => (
        <Tag color={record.enable_evaluation ? 'purple' : 'default'}>
          {record.enable_evaluation ? 'Kích hoạt' : 'Tắt'}
        </Tag>
      ),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 140,
      render: (_: unknown, record: MeetingResponse) => (
        <Space size="small">
          {onView && (
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onView(record)}
              title="Xem chi tiết"
            />
          )}
          {canUpdate && onEdit && (
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit(record)}
              title="Chỉnh sửa"
            />
          )}
          {canDelete && onDelete && (
            <Popconfirm
              title="Xóa buổi họp này?"
              description="Hành động này không thể hoàn tác."
              onConfirm={() => onDelete(record.id)}
              okText="Xóa"
              cancelText="Hủy"
            >
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
                title="Xóa"
              />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={meetings}
      rowKey="id"
      loading={isLoading}
      pagination={paginationProps}
      className="border border-gray-100 rounded-lg custom-table"
    />
  );
};

export default MeetingTable;
