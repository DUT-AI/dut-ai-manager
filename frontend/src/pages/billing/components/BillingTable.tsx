import { Table, Space, Avatar, Typography, Tag, Button, Popconfirm } from 'antd';
import { UserOutlined, EyeOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { InvoiceStatus } from '@/types/billing.types';
import type { Invoice, InvoiceStatusType } from '@/types/billing.types';
import type { UserResponse } from '@/types/user.types';

const { Text } = Typography;

interface BillingTableProps {
  invoices: Invoice[];
  isLoading: boolean;
  users: UserResponse[];
  onViewDetail: (id: number) => void;
  onEdit?: (invoice: Invoice) => void;
  onDelete: (id: number) => void;
  deletingId: number | null;
}

const BillingTable = ({
  invoices,
  isLoading,
  users,
  onViewDetail,
  onEdit,
  onDelete,
  deletingId
}: BillingTableProps) => {
  const columns = [
    {
      title: 'Mã hóa đơn',
      dataIndex: 'reference_code',
      key: 'reference_code',
      render: (code: string) => <Text strong>{code}</Text>,
    },
    {
      title: 'Thành viên',
      key: 'user',
      render: (_: any, record: Invoice) => {
        const user = users.find(u => u.id === record.user_id);
        return (
          <Space>
            <Avatar src={user?.avatar_url || ''} icon={<UserOutlined />} size="small" />
            <Text>{user?.name || `User ID: ${record.user_id}`}</Text>
          </Space>
        );
      }
    },
    {
      title: 'Số tiền',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <Text strong>{amount.toLocaleString()} VNĐ</Text>,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status: InvoiceStatusType) => {
        const colors: Record<string, string> = {
          [InvoiceStatus.PENDING]: 'orange',
          [InvoiceStatus.PAID]: 'green',
          [InvoiceStatus.CANCELLED]: 'red',
          [InvoiceStatus.EXPIRED]: 'gray',
        };
        return <Tag color={colors[status]}>{status}</Tag>;
      },
    },
    {
      title: 'Kỳ hóa đơn',
      dataIndex: 'billing_period',
      key: 'billing_period',
      render: (date: string) => dayjs(date).format('MM/YYYY'),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_: any, record: Invoice) => (
        <Space>
          <Button 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => onViewDetail(record.id)}
          >
            Chi tiết
          </Button>
          {record.status !== InvoiceStatus.PAID && (
            <Button 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => onEdit && onEdit(record)}
            />
          )}
          <Popconfirm
            title="Xóa hóa đơn?"
            description="Hành động này không thể hoàn tác."
            onConfirm={() => onDelete(record.id)}
            disabled={record.status === InvoiceStatus.PAID}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger 
              disabled={record.status === InvoiceStatus.PAID}
              loading={deletingId === record.id}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      dataSource={invoices}
      columns={columns}
      rowKey="id"
      loading={isLoading}
      pagination={{ pageSize: 15 }}
      scroll={{ x: 'max-content' }}
    />
  );
};

export default BillingTable;
