import { Table, Space, Avatar, Typography, Tag, Button, Popconfirm, Tooltip, type TablePaginationConfig } from 'antd';
import { UserOutlined, EyeOutlined, DeleteOutlined, EditOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { type Invoice, InvoiceStatus } from '@/types';
import type { UserResponse } from '@/features/users/types/user.types';
import { useAuth } from '@/features/auth';
import { BillingPermission } from '@/features/rbac/types/rbac.types';

const { Text } = Typography;

export interface BillingTableUserItem {
  id: number;
  name: string;
  avatar_url?: string | null;
  email?: string;
}

interface BillingTableProps {
  invoices: Invoice[];
  isLoading: boolean;
  users: Array<UserResponse | BillingTableUserItem>;
  onViewDetail: (id: number) => void;
  onEdit?: (invoice: Invoice) => void;
  onDelete: (id: number) => void;
  deletingId: number | null;
  pagination?: TablePaginationConfig | false;
  onUpdateStatus?: (id: number, status: InvoiceStatus) => void;
  updatingStatusId?: number | null;
}

const BillingTable = ({
  invoices,
  isLoading,
  users,
  onViewDetail,
  onEdit,
  onDelete,
  deletingId,
  pagination,
  onUpdateStatus,
  updatingStatusId,
}: BillingTableProps) => {
  const { hasPermission } = useAuth();
  const canUpdate = hasPermission(BillingPermission.UPDATE);
  const canDelete = hasPermission(BillingPermission.DELETE);

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
      render: (_: unknown, record: Invoice) => {
        const isPaid = record.status === InvoiceStatus.PAID;
        const statusTooltip = !canUpdate
          ? 'Bạn không có quyền cập nhật trạng thái hóa đơn'
          : isPaid
            ? 'Chuyển về chờ thanh toán'
            : 'Đánh dấu đã nộp tiền';

        const editTooltip = !canUpdate
          ? 'Bạn không có quyền chỉnh sửa hóa đơn'
          : 'Sửa hóa đơn';

        const deleteTooltip = !canDelete
          ? 'Bạn không có quyền xóa hóa đơn'
          : isPaid
            ? 'Không thể xóa hóa đơn đã thanh toán'
            : 'Xóa hóa đơn';

        return (
          <Space>
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => onViewDetail(record.id)}
            >
              Chi tiết
            </Button>

            {onUpdateStatus && (
              <Tooltip title={statusTooltip}>
                <span className="inline-block">
                  <Popconfirm
                    title={
                      isPaid
                        ? 'Chuyển về Chưa thanh toán?'
                        : 'Xác nhận bạn này đã nộp tiền?'
                    }
                    description={
                      isPaid
                        ? 'Hóa đơn sẽ chuyển lại về PENDING.'
                        : 'Hóa đơn sẽ được đánh dấu đã nộp (PAID).'
                    }
                    onConfirm={() =>
                      onUpdateStatus(
                        record.id,
                        isPaid ? InvoiceStatus.PENDING : InvoiceStatus.PAID
                      )
                    }
                    okText="Đồng ý"
                    cancelText="Hủy"
                    disabled={!canUpdate}
                  >
                    <Button
                      size="small"
                      disabled={!canUpdate || updatingStatusId === record.id}
                      className={
                        !canUpdate
                          ? 'opacity-50 cursor-not-allowed'
                          : isPaid
                            ? 'text-amber-600 border-amber-300 hover:text-amber-700'
                            : 'text-emerald-600 border-emerald-300 hover:text-emerald-700'
                      }
                      icon={isPaid ? <ClockCircleOutlined /> : <CheckCircleOutlined />}
                      loading={updatingStatusId === record.id}
                    >
                      {isPaid ? 'Hủy gạch nợ' : 'Đã nộp'}
                    </Button>
                  </Popconfirm>
                </span>
              </Tooltip>
            )}

            <Tooltip title={editTooltip}>
              <span className="inline-block">
                <Button
                  icon={<EditOutlined />}
                  size="small"
                  disabled={!canUpdate}
                  className={!canUpdate ? 'opacity-50 cursor-not-allowed' : undefined}
                  onClick={() => onEdit && onEdit(record)}
                />
              </span>
            </Tooltip>

            <Tooltip title={deleteTooltip}>
              <span className="inline-block">
                <Popconfirm
                  title="Xóa hóa đơn?"
                  description="Hành động này không thể hoàn tác."
                  onConfirm={() => onDelete(record.id)}
                  disabled={!canDelete || isPaid}
                  okText="Xóa"
                  cancelText="Hủy"
                  okButtonProps={{ danger: true }}
                >
                  <Button
                    icon={<DeleteOutlined />}
                    size="small"
                    danger
                    disabled={!canDelete || isPaid}
                    className={!canDelete ? 'opacity-50 cursor-not-allowed' : undefined}
                    loading={deletingId === record.id}
                  />
                </Popconfirm>
              </span>
            </Tooltip>
          </Space>
        );
      },
    },
  ];

  return (
    <Table
      dataSource={invoices}
      columns={columns}
      rowKey="id"
      loading={isLoading}
      pagination={pagination !== undefined ? pagination : { pageSize: 20 }}
      scroll={{ x: 'max-content' }}
    />
  );
};

export default BillingTable;
