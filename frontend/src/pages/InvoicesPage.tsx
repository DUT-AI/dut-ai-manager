import { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Tag,
  Button,
  Typography,
  Modal,
  Space,
  Empty,
  Spin,
  message,
  Descriptions,
  Divider,
  Grid
} from 'antd';
import {
  CreditCardOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useMyInvoices, useInvoiceDetail } from '@/hooks/useBilling';
import { useViolations } from '@/hooks';
import { InvoiceStatus } from '@/types/billing.types';
import type { InvoiceStatusType } from '@/types/billing.types';
import dayjs from 'dayjs';
import { motion, type Variants } from 'motion/react';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

const StatusTag = ({ status }: { status: InvoiceStatusType }) => {
  switch (status) {
    case InvoiceStatus.PAID:
      return <Tag color="success" icon={<CheckCircleOutlined />}>Đã thanh toán</Tag>;
    case InvoiceStatus.PENDING:
      return <Tag color="warning" icon={<ClockCircleOutlined />}>Chờ thanh toán</Tag>;
    case InvoiceStatus.CANCELLED:
      return <Tag color="error" icon={<CloseCircleOutlined />}>Đã hủy</Tag>;
    default:
      return <Tag color="default">{status}</Tag>;
  }
};

const InvoicesPage = () => {
  const screens = useBreakpoint();
  const { data: invoices, isLoading } = useMyInvoices();
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Polling only when PENDING invoice is selected and modal is open
  const { data: detail } = useInvoiceDetail(
    selectedInvoiceId || 0,
    isModalOpen,
    selectedInvoiceId && invoices?.find(i => i.id === selectedInvoiceId)?.status === InvoiceStatus.PENDING ? 5000 : undefined
  );

  const match = detail?.description.match(/tháng\s+(\d{2})\/(\d{4})/i);
  const month = match ? parseInt(match[1]) : (detail ? dayjs(detail.created_at).month() + 1 : undefined);
  const year = match ? parseInt(match[2]) : (detail ? dayjs(detail.created_at).year() : undefined);

  const hasViolation = detail?.items.some(item => item.item_type === 'VIOLATION');

  const { data: violations = [], isLoading: isViolationsLoading } = useViolations({
    userId: detail?.user_id,
    month,
    year,
    enabled: isModalOpen && !!detail && !!hasViolation && !!month && !!year
  });

  useEffect(() => {
    if (detail?.status === InvoiceStatus.PAID && isModalOpen) {
      message.success('Thanh toán thành công! Hóa đơn đã được ghi nhận.');
      // Keep modal open but polling will stop due to status change if we use the logic in useInvoiceDetail
    }
  }, [detail?.status, isModalOpen]);

  const columns = [
    {
      title: 'Mã hóa đơn',
      dataIndex: 'reference_code',
      key: 'reference_code',
      render: (code: string) => <Text strong className="text-blue-600">{code}</Text>,
    },
    {
      title: 'Mô tả',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Số tiền',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <Text strong>{amount.toLocaleString()} VNĐ</Text>,
    },
    {
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY HH:mm'),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (status: InvoiceStatusType) => <StatusTag status={status} />,
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_: any, record: any) => (
        <Button 
          type="primary" 
          ghost 
          icon={<EyeOutlined />} 
          size="small"
          onClick={() => {
            setSelectedInvoiceId(record.id);
            setIsModalOpen(true);
          }}
        >
          {record.status === InvoiceStatus.PENDING ? 'Thanh toán' : 'Chi tiết'}
        </Button>
      ),
    },
  ];

  return (
    <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="p-4 md:p-6 bg-[#f8fafc] min-h-full"
    >
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
        <Space size="middle">
          <div className="hidden md:flex w-12 h-12 rounded-xl bg-blue-50 items-center justify-center text-blue-600 shadow-sm">
            <CreditCardOutlined className="text-2xl" />
          </div>
          <div>
            <Title level={3} className="text-xl md:text-2xl mt-4 text-blue-600">Hóa đơn của tôi</Title>
            <Text type="secondary" className="text-xs md:text-sm">Xem lịch sử và thực hiện thanh toán</Text>
          </div>
        </Space>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card 
            className="shadow-sm border-gray-100 rounded-xl overflow-hidden"
            styles={{ body: { padding: '0' } }}
        >
            <Table
            dataSource={invoices}
            columns={columns}
            rowKey="id"
            loading={isLoading}
            locale={{ emptyText: <Empty description="Bạn chưa có hóa đơn nào" /> }}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 'max-content' }}
            />
        </Card>
      </motion.div>

      <Modal
        title={`Chi tiết hóa đơn ${detail?.reference_code || ''}`}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          setSelectedInvoiceId(null);
        }}
        footer={null}
        width={screens.md ? 600 : '95%'}
        centered
        destroyOnClose
      >
        {detail ? (
          <div className="py-2">
            <div className="flex justify-between items-center mb-6">
              <StatusTag status={detail.status} />
              <Text type="secondary">{dayjs(detail.created_at).format('DD/MM/YYYY HH:mm')}</Text>
            </div>

            <Descriptions column={1} bordered size="small" className="mb-6">
              <Descriptions.Item label="Nội dung">{detail.description}</Descriptions.Item>
              <Descriptions.Item label="Số tiền">
                <Title level={4} className="mb-0! text-blue-600">{detail.amount.toLocaleString()} VNĐ</Title>
              </Descriptions.Item>
              <Descriptions.Item label="Mã tham chiếu">
                <Text copyable strong>{detail.reference_code}</Text>
              </Descriptions.Item>
            </Descriptions>

            {detail.items && detail.items.length > 0 && (
              <div className="mb-6">
                <Divider>Chi tiết các mục</Divider>
                <Table
                  dataSource={detail.items}
                  pagination={false}
                  size="small"
                  rowKey="id"
                  columns={[
                    { title: 'Hạng mục', dataIndex: 'note', key: 'note' },
                    { title: 'Loại', dataIndex: 'item_type', key: 'item_type', render: (t) => <Tag>{t}</Tag> },
                    { title: 'Tiền', dataIndex: 'amount', key: 'amount', render: (a) => a.toLocaleString() },
                  ]}
                />
              </div>
            )}

            {hasViolation && violations.length > 0 && (
              <div className="mb-6">
                <Divider>
                  <Space className="text-red-500 font-semibold">
                    <WarningOutlined /> Chi tiết các lỗi vi phạm tháng {month && year ? `${month.toString().padStart(2, '0')}/${year}` : ''}
                  </Space>
                </Divider>
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

            {detail.status === InvoiceStatus.PENDING && (
              <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 flex flex-col items-center">
                <Space direction="vertical" align="center" size="middle" className="w-full">
                  <div className="bg-white p-3 rounded-xl shadow-md">
                    <img 
                      src={detail.qr_url} 
                      alt="VietQR Payment" 
                      className="w-full max-w-[280px] aspect-square object-contain"
                    />
                  </div>
                  <div className="text-center">
                    <Title level={5} className="mb-1!">Quét mã để thanh toán</Title>
                    <Text type="secondary" className="text-sm">Vui lòng không sửa nội dung chuyển khoản để hệ thống tự động xác nhận</Text>
                  </div>
                  <div className="flex items-center gap-2 text-blue-600 bg-white px-4 py-2 rounded-full border border-blue-100 animate-pulse">
                    <Spin size="small" />
                    <Text className="text-blue-600 font-medium">Đang chờ thanh toán...</Text>
                  </div>
                </Space>
              </div>
            )}

            {detail.status === InvoiceStatus.PAID && (
              <div className="bg-green-50 p-8 rounded-2xl border border-green-100 flex flex-col items-center text-center">
                <CheckCircleOutlined className="text-5xl text-green-500 mb-4" />
                <Title level={4} className="text-green-700">Thanh toán hoàn tất</Title>
                <Text>Mã giao dịch: <Text strong>{detail.transaction_id || 'N/A'}</Text></Text>
                <Button 
                  type="primary" 
                  className="mt-6 bg-green-600 border-none h-10 px-8 rounded-lg"
                  onClick={() => setIsModalOpen(false)}
                >
                  Đóng
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="py-12 flex justify-center">
            <Spin tip="Đang tải..." />
          </div>
        )}
      </Modal>
    </motion.div>
  );
};

export default InvoicesPage;
