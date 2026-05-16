import { Modal, Space, Descriptions, Avatar, Typography, Tag, Table, Spin } from 'antd';
import { InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { InvoiceStatus } from '@/types/billing.types';
import type { Invoice } from '@/types/billing.types';
import type { UserResponse } from '@/types/user.types';
import { useViolations } from '@/hooks';

const { Title, Text } = Typography;

interface InvoiceDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  detail: Invoice | null | undefined;
  users: UserResponse[];
  isMobile?: boolean;
}

const InvoiceDetailModal = ({
  isOpen,
  onClose,
  detail,
  users,
  isMobile
}: InvoiceDetailModalProps) => {
  const user = users.find(u => u.id === detail?.user_id);

  const match = detail?.description.match(/tháng\s+(\d{2})\/(\d{4})/i);
  const month = match ? parseInt(match[1]) : (detail ? dayjs(detail.created_at).month() + 1 : undefined);
  const year = match ? parseInt(match[2]) : (detail ? dayjs(detail.created_at).year() : undefined);

  const hasViolation = detail?.items.some(item => item.item_type === 'VIOLATION');

  const { data: violations = [], isLoading: isViolationsLoading } = useViolations({
    userId: detail?.user_id,
    month,
    year,
    enabled: isOpen && !!detail && !!hasViolation && !!month && !!year
  });

  return (
    <Modal
      title={
        <Space>
          <InfoCircleOutlined className="text-indigo-600" />
          <span>Chi tiết hóa đơn {detail?.reference_code}</span>
        </Space>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={isMobile ? '95%' : 600}
      centered
    >
      {detail ? (
        <div className="py-2">
          <Descriptions column={2} bordered size="small" className="mb-6">
            <Descriptions.Item label="Thành viên" span={2}>
              <Space>
                <Avatar src={user?.avatar_url || ''} size="small" />
                <Text strong>{user?.name || `User ID: ${detail.user_id}`}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="Ngày tạo">{dayjs(detail.created_at).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
            <Descriptions.Item label="Trạng thái">
              <Tag color={detail.status === InvoiceStatus.PAID ? 'green' : 'orange'}>{detail.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Mã tham chiếu" span={2}><Text strong>{detail.reference_code}</Text></Descriptions.Item>
            <Descriptions.Item label="Mã giao dịch" span={2}>{detail.transaction_id || 'Chưa có'}</Descriptions.Item>
            <Descriptions.Item label="Tổng tiền" span={2}>
              <Title level={4} className="mb-0! text-indigo-600">{detail.amount.toLocaleString()} VNĐ</Title>
            </Descriptions.Item>
          </Descriptions>

          <Title level={5} className="mb-3">Danh sách hạng mục</Title>
          <Table
            dataSource={detail.items}
            pagination={false}
            size="small"
            rowKey="id"
            columns={[
              { title: 'Nội dung', dataIndex: 'note', key: 'note' },
              { title: 'Loại', dataIndex: 'item_type', key: 'item_type' },
              { title: 'Tiền', dataIndex: 'amount', key: 'amount', render: (a) => a.toLocaleString() },
            ]}
            className="border border-gray-100 rounded-lg overflow-hidden mb-6"
          />

          {hasViolation && violations.length > 0 && (
            <div>
              <Title level={5} className="mb-3 text-red-600 flex items-center gap-2">
                <WarningOutlined /> Chi tiết các lỗi vi phạm tháng {month && year ? `${month.toString().padStart(2, '0')}/${year}` : ''}
              </Title>
              <Table
                dataSource={violations}
                loading={isViolationsLoading}
                pagination={false}
                size="small"
                rowKey="id"
                columns={[
                  { 
                    title: 'Ngày vi phạm', 
                    dataIndex: 'date', 
                    key: 'date',
                    width: 140,
                    render: (d) => dayjs(d).format('DD/MM/YYYY')
                  },
                  { 
                    title: 'Lý do', 
                    dataIndex: 'reason', 
                    key: 'reason' 
                  },
                ]}
                className="border border-red-100 rounded-lg overflow-hidden bg-red-50/10"
              />
            </div>
          )}
        </div>
      ) : (
        <div className="py-12 flex justify-center"><Spin /></div>
      )}
    </Modal>
  );
};

export default InvoiceDetailModal;
