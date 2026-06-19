import { useState } from 'react';
import {
  Modal,
  Form,
  Select,
  DatePicker,
  InputNumber,
  Button,
  Divider,
  Table,
  Space,
  Typography,
  message,
  Alert,
  Input
} from 'antd';
import { 
  HistoryOutlined, 
  TeamOutlined, 
  UserOutlined, 
  PlusOutlined, 
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUsers, useTeams } from '@/hooks';
import { useCreateMonthlyInvoices } from '@/hooks/useBilling';
import { InvoiceItemType } from '@/types/billing.types';
import type { MonthlyInvoiceItemPreview } from '@/types/billing.types';

const { Title, Text } = Typography;
const { Option } = Select;

interface CreateMonthlyInvoiceModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const CreateMonthlyInvoiceModal = ({ open, onCancel, onSuccess }: CreateMonthlyInvoiceModalProps) => {
  const [form] = Form.useForm();
  const { data: users = [] } = useUsers();
  const { data: teams = [] } = useTeams();
  const createMonthly = useCreateMonthlyInvoices();
  
  const [previewData, setPreviewData] = useState<MonthlyInvoiceItemPreview[]>([]);
  const [isPreviewing, setIsPreviewing] = useState(false);

  const handlePreview = async () => {
    try {
      const values = await form.validateFields();
      setIsPreviewing(true);
      
      const payload = {
        month: values.billing_period.month() + 1,
        year: values.billing_period.year(),
        team_id: values.team_id,
        user_ids: values.user_ids || [],
        violation_price: values.violation_price,
        fund_amount: values.fund_amount,
        extra_items: values.extra_items || [],
        execute: false
      };

      const response = await createMonthly.mutateAsync(payload);
      const data = response.data as any;
      setPreviewData(data.items || []);
      message.success('Đã làm mới bản xem trước');
    } catch (error: any) {
      console.error(error);
      message.error(error?.response?.data?.message || 'Có lỗi khi lấy bản xem trước');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleExecute = async () => {
    try {
      const values = await form.validateFields();
      
      const payload = {
        month: values.billing_period.month() + 1,
        year: values.billing_period.year(),
        team_id: values.team_id,
        user_ids: values.user_ids || [],
        violation_price: values.violation_price,
        fund_amount: values.fund_amount,
        extra_items: values.extra_items || [],
        execute: true
      };

      await createMonthly.mutateAsync(payload);
      message.success('Đã tạo hóa đơn hàng loạt thành công');
      onSuccess();
      onCancel();
      form.resetFields();
      setPreviewData([]);
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Có lỗi xảy ra khi tạo hóa đơn');
    }
  };

  const columns = [
    {
      title: 'Thành viên',
      dataIndex: 'user_name',
      key: 'user_name',
      render: (name: string) => <Text strong>{name}</Text>
    },
    {
      title: 'Vi phạm',
      key: 'violations',
      render: (_: any, record: MonthlyInvoiceItemPreview) => (
        <Space direction="vertical" size={0}>
          <Text>{record.violation_count} lỗi</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>({record.violation_amount.toLocaleString()} đ)</Text>
        </Space>
      )
    },
    {
      title: 'Tiền quỹ',
      dataIndex: 'fund_amount',
      key: 'fund_amount',
      render: (amount: number) => <span>{amount.toLocaleString()} đ</span>
    },
    {
      title: 'Tổng cộng',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number) => <Text strong className="text-indigo-600">{amount.toLocaleString()} đ</Text>
    }
  ];

  return (
    <Modal
      title={
        <Space>
          <div className="bg-indigo-50 p-2 rounded-lg text-indigo-600">
            <HistoryOutlined className="text-xl" />
          </div>
          <Title level={4} className="mb-0!">Tạo hóa đơn tháng hàng loạt</Title>
        </Space>
      }
      open={open}
      onCancel={onCancel}
      width={900}
      footer={[
        <Button key="cancel" onClick={onCancel}>Hủy</Button>,
        <Button 
          key="preview" 
          icon={<EyeOutlined />} 
          onClick={handlePreview}
          loading={isPreviewing}
        >
          Xem trước
        </Button>,
        <Button 
          key="submit" 
          type="primary" 
          icon={<CheckCircleOutlined />}
          onClick={handleExecute}
          className="bg-indigo-600 border-none"
          loading={createMonthly.isPending}
        >
          Tạo {previewData.length > 0 ? `${previewData.length} hóa đơn` : ''}
        </Button>
      ]}
      centered
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ 
          billing_period: dayjs(), 
          violation_price: 20000, 
          fund_amount: 50000,
          extra_items: [] 
        }}
        className="mt-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item
            name="billing_period"
            label="Kỳ hóa đơn (Tháng/Năm)"
            rules={[{ required: true, message: 'Vui lòng chọn kỳ hóa đơn' }]}
          >
            <DatePicker picker="month" className="w-full" format="MM/YYYY" placeholder="Chọn tháng/năm" />
          </Form.Item>

          <Form.Item
            name="team_id"
            label="Chọn Team (Tùy chọn)"
          >
            <Select 
              placeholder="Chọn team để áp dụng cho tất cả thành viên" 
              allowClear
            >
              {(teams ?? []).map(t => (
                <Option key={t.id} value={t.id}>{t.team_name}</Option>
              ))}
            </Select>
          </Form.Item>
        </div>

        <Form.Item
          name="user_ids"
          label="Hoặc chọn thành viên cụ thể"
        >
          <Select 
            mode="multiple" 
            placeholder="Chọn 1 hoặc nhiều thành viên"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {users.map(u => (
              <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>
            ))}
          </Select>
        </Form.Item>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
          <Form.Item
            name="violation_price"
            label="Đơn giá 1 vi phạm (VNĐ)"
            rules={[{ required: true }]}
          >
            <InputNumber 
              className="w-full" 
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value?.replace(/\$\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item
            name="fund_amount"
            label="Tiền quỹ tháng (VNĐ)"
            rules={[{ required: true }]}
          >
            <InputNumber 
              className="w-full" 
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value?.replace(/\$\s?|(,*)/g, '') as any}
            />
          </Form.Item>
        </div>

        <Divider orientation="left">Hạng mục bổ sung (Tùy chọn)</Divider>
        <Form.List name="extra_items">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} wrap style={{ display: 'flex', marginBottom: 16 }} align="baseline" className="bg-gray-50 p-3 rounded-lg border border-dashed border-gray-200">
                  <Form.Item
                    {...restField}
                    name={[name, 'item_type']}
                    rules={[{ required: true, message: 'Chọn loại' }]}
                    style={{ width: 140, marginBottom: 0 }}
                  >
                    <Select placeholder="Loại">
                      <Option value={InvoiceItemType.DINING}>Ăn uống</Option>
                      <Option value={InvoiceItemType.OTHER}>Khác</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item
                    {...restField}
                    name={[name, 'note']}
                    rules={[{ required: true, message: 'Nhập nội dung' }]}
                    style={{ marginBottom: 0 }}
                  >
                    <Input placeholder="Nội dung" style={{ width: 250 }} />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'amount']}
                    rules={[{ required: true, message: 'Nhập tiền' }]}
                    style={{ marginBottom: 0 }}
                  >
                    <InputNumber 
                      min={0} 
                      formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => (value?.replace(/\$\s?|(,*)/g, '') || 0) as any}
                      placeholder="Số tiền" 
                      style={{ width: 150 }} 
                    />
                  </Form.Item>

                  <Button type="text" danger icon={<DeleteOutlined />} onClick={() => remove(name)} />
                </Space>
              ))}
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />} className="mt-2">
                Thêm hạng mục bổ sung
              </Button>
            </>
          )}
        </Form.List>

        {previewData.length > 0 && (
          <div className="mt-6">
            <Divider orientation="left">Bản xem trước ({previewData.length} người dùng)</Divider>
            <Table 
              dataSource={previewData} 
              columns={columns} 
              rowKey="user_id" 
              pagination={{ pageSize: 5 }}
              size="small"
              className="border border-gray-100 rounded-lg overflow-hidden"
            />
            <Alert 
              message="Lưu ý: Chỉ những thành viên có số tiền > 0 mới được tạo hóa đơn." 
              type="info" 
              showIcon 
              className="mt-3" 
            />
          </div>
        )}
      </Form>
    </Modal>
  );
};

export default CreateMonthlyInvoiceModal;
