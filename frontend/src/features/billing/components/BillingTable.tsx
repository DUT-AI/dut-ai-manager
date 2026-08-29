import { Table, Space, Avatar, Typography, Tag, Button, Popconfirm } from 'antd';
import { UserOutlined, EyeOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { type Invoice, InvoiceStatus } from '@/types';
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
      key: 'reference_code',
      render: (_: unknown, record: Invoice) => <Text strong>{record.reference_code || record.invoice_code || 'N/A'}</Text>,
    },
    {
      title: 'Thành viên',
      key: 'user',
      render: (_: unknown, record: Invoice) => {
        const user = users.find(u => u.id === record.user_id);
        return (
          <Space>
            <Avatar src={user?.avatar_url || undefined} icon={<UserOutlined />} size="small" />
            <Text>{user?.name || `User ID: ${record.user_id}`}</Text>
          </Space>
        );
      }
    },
    {
      title: 'Nhóm',
      key: 'team',
      render: (_: unknown, record: Invoice) => (
        <Tag color="blue">{record.team?.team_name || record.team_name || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Số tiền',
      key: 'amount',
      render: (_: unknown, record: Invoice) => <Text strong>{(Number(record.amount ?? record.total_amount) || 0).toLocaleString()} VNĐ</Text>,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status: InvoiceStatus) => {
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
      render: (_: unknown, record: Invoice) => (
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
