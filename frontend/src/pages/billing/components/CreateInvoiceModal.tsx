import { Modal, Form, Select, Input, Divider, Space, InputNumber, Button } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { InvoiceItemType } from '@/types/billing.types';
import type { UserResponse } from '@/types/user.types';

const { Option } = Select;

interface CreateInvoiceModalProps {
  isOpen: boolean;
  onCancel: () => void;
  onFinish: (values: any) => void;
  loading: boolean;
  users: UserResponse[];
  form: any;
}

const CreateInvoiceModal = ({
  isOpen,
  onCancel,
  onFinish,
  loading,
  users,
  form
}: CreateInvoiceModalProps) => {
  return (
    <Modal
      title="Tạo hóa đơn mới"
      open={isOpen}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={loading}
      width={700}
      okText="Tạo hóa đơn"
      cancelText="Hủy"
      centered
      destroyOnClose
    >
      <Form 
        form={form} 
        layout="vertical" 
        onFinish={onFinish}
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
  );
};

export default CreateInvoiceModal;
