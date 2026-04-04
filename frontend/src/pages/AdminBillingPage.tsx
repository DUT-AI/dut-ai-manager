import { useState } from 'react';
import {
  Table,
  Card,
  Button,
  Typography,
  Modal,
  Space,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Alert,
  Tag,
  Divider,
  Avatar,
  Grid,
  Descriptions,
  Spin
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  UserOutlined,
  AuditOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAllInvoices, useCreateInvoice, useInvoiceDetail } from '@/hooks/useBilling';
import { useUsers } from '@/hooks';
import { InvoiceStatus, InvoiceItemType } from '@/types/billing.types';
import CreateMonthlyInvoiceModal from '@/components/billing/CreateMonthlyInvoiceModal';
import type { InvoiceStatusType, InvoiceCreate } from '@/types/billing.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { useBreakpoint } = Grid;

const AdminBillingPage = () => {
  const screens = useBreakpoint();
  const { data: invoices, isLoading } = useAllInvoices();
  const { data: users = [] } = useUsers();
  const createInvoice = useCreateInvoice();
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isMonthlyModalOpen, setIsMonthlyModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [form] = Form.useForm();

  const { data: detail } = useInvoiceDetail(selectedInvoiceId || 0, isDetailModalOpen);

  const handleCreate = async (values: any) => {
    try {
      const payload: InvoiceCreate = {
        user_id: values.user_id,
        description: values.description,
        items: values.items.map((item: any) => ({
          item_type: item.item_type,
          amount: item.amount,
          note: item.note
        }))
      };
      
      await createInvoice.mutateAsync(payload);
      message.success('Tạo hóa đơn thành công');
      setIsCreateModalOpen(false);
      form.resetFields();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Có lỗi xảy ra khi tạo hóa đơn');
    }
  };

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
      render: (_: any, record: any) => {
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
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_: any, record: any) => (
        <Button 
          icon={<EyeOutlined />} 
          size="small"
          onClick={() => {
            setSelectedInvoiceId(record.id);
            setIsDetailModalOpen(true);
          }}
        >
          Chi tiết
        </Button>
      ),
    },
  ];

  return (
    <div className="p-4 md:p-6 bg-[#f8fafc] min-h-full">
      <Card 
        className="shadow-sm border-gray-100 rounded-xl overflow-hidden"
        title={
          <Space>
            <div className="bg-indigo-50 p-2 rounded-lg text-indigo-600">
              <AuditOutlined className="text-xl" />
            </div>
            <div>
              <Title level={4} className="mb-0!">Quản lý Hóa đơn</Title>
              <Text type="secondary" className="text-xs font-normal">Công cụ dành cho quản trị viên</Text>
            </div>
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<CalendarOutlined />} 
              onClick={() => setIsMonthlyModalOpen(true)}
              className="h-10 px-6 font-semibold rounded-lg border-indigo-200 text-indigo-600 hover:text-indigo-700 hover:border-indigo-300"
            >
              Tạo hóa đơn tháng
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => setIsCreateModalOpen(true)}
              className="bg-indigo-600 border-none h-10 px-6 font-semibold rounded-lg"
            >
              Tạo hóa đơn
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={invoices}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 15 }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* Create Modal */}
      <Modal
        title="Tạo hóa đơn mới"
        open={isCreateModalOpen}
        onCancel={() => setIsCreateModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createInvoice.isPending}
        width={700}
        okText="Tạo hóa đơn"
        cancelText="Hủy"
        centered
        destroyOnClose
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={handleCreate}
          initialValues={{ items: [{ item_type: InvoiceItemType.VIOLATION, amount: 20000 }] }}
          className="mt-4"
        >
          <Form.Item 
            name="user_id" 
            label="Chọn thành viên" 
            rules={[{ required: true, message: 'Vui lòng chọn thành viên' }]}
          >
            <Select 
              showSearch 
              placeholder="Tìm kiếm theo tên hoặc email"
              optionFilterProp="children"
            >
              {users.map(u => (
                <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="description" label="Ghi chú tổng quát">
            <Input placeholder="Ví dụ: Phí sinh hoạt và vi phạm tháng 3" />
          </Form.Item>

          <Divider>Danh sách hạng mục</Divider>
          
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline" className="bg-gray-50 p-3 rounded-lg border border-dashed border-gray-200">
                    <Form.Item
                      {...restField}
                      name={[name, 'item_type']}
                      rules={[{ required: true, message: 'Chọn loại' }]}
                      style={{ width: 130 }}
                    >
                      <Select placeholder="Loại">
                        <Option value={InvoiceItemType.VIOLATION}>Vi phạm</Option>
                        <Option value={InvoiceItemType.FUND}>Tiền quỹ</Option>
                        <Option value={InvoiceItemType.DINING}>Ăn uống</Option>
                        <Option value={InvoiceItemType.OTHER}>Khác</Option>
                      </Select>
                    </Form.Item>
                    
                    <Form.Item
                      {...restField}
                      name={[name, 'note']}
                      rules={[{ required: true, message: 'Nhập nội dung' }]}
                    >
                      <Input placeholder="Nội dung cụ thể (vd: Đi muộn 01/03)" style={{ width: 250 }} />
                    </Form.Item>

                    <Form.Item
                      {...restField}
                      name={[name, 'amount']}
                      rules={[{ required: true, message: 'Nhập số tiền' }]}
                    >
                      <InputNumber 
                        min={0} 
                        formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                        parser={value => (value?.replace(/\$\s?|(,*)/g, '') || 0) as any}
                        placeholder="Số tiền" 
                        style={{ width: 150 }} 
                      />
                    </Form.Item>

                    <Button 
                      type="text" 
                      danger 
                      icon={<DeleteOutlined />} 
                      onClick={() => remove(name)} 
                      disabled={fields.length === 1}
                    />
                  </Space>
                ))}
                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    Thêm hạng mục
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* Detail Modal */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined className="text-indigo-600" />
            <span>Chi tiết hóa đơn {detail?.reference_code}</span>
          </Space>
        }
        open={isDetailModalOpen}
        onCancel={() => {
          setIsDetailModalOpen(false);
          setSelectedInvoiceId(null);
        }}
        footer={null}
        width={screens.md ? 600 : '95%'}
        centered
      >
        {detail ? (
          <div className="py-2">
            <Descriptions column={2} bordered size="small" className="mb-6">
              <Descriptions.Item label="Thành viên" span={2}>
                <Space>
                  <Avatar src={users.find(u => u.id === detail.user_id)?.avatar_url || ''} size="small" />
                  <Text strong>{users.find(u => u.id === detail.user_id)?.name}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Ngày tạo">{dayjs(detail.created_at).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
              <Descriptions.Item label="Trạng thái"><Tag color={detail.status === InvoiceStatus.PAID ? 'green' : 'orange'}>{detail.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="Mã tham chiếu" span={2}><Text strong>{detail.reference_code}</Text></Descriptions.Item>
              <Descriptions.Item label="Mã giao dịch" span={2}>{detail.transaction_id || 'Chưa có'}</Descriptions.Item>
              <Descriptions.Item label="Tổng tiền" span={2}><Title level={4} className="mb-0! text-indigo-600">{detail.amount.toLocaleString()} VNĐ</Title></Descriptions.Item>
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
              className="border border-gray-100 rounded-lg overflow-hidden"
            />
          </div>
        ) : (
          <div className="py-12 flex justify-center"><Spin /></div>
        )}
      </Modal>

      {/* Monthly Create Modal */}
      <CreateMonthlyInvoiceModal 
        open={isMonthlyModalOpen}
        onCancel={() => setIsMonthlyModalOpen(false)}
        onSuccess={() => {
          // Success message handled in modal
        }}
      />
    </div>
  );
};

export default AdminBillingPage;
