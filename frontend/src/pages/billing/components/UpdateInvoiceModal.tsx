import { Modal, Form, Select, Input, Divider, Space, InputNumber, Button } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { InvoiceItemType } from '@/types/billing.types';
import type { Invoice } from '@/types/billing.types';
import { useEffect } from 'react';

const { Option } = Select;

interface UpdateInvoiceModalProps {
  isOpen: boolean;
  onCancel: () => void;
  onFinish: (values: any) => void;
  loading: boolean;
  invoice: Invoice | null;
  form: any;
}

const UpdateInvoiceModal = ({
  isOpen,
  onCancel,
  onFinish,
  loading,
  invoice,
  form
}: UpdateInvoiceModalProps) => {

  useEffect(() => {
    if (isOpen && invoice) {
      form.setFieldsValue({
        description: invoice.description,
        items: invoice.items.map(item => ({
          item_type: item.item_type,
          note: item.note,
          amount: item.amount,
          reference_id: item.reference_id,
        })),
      });
    } else {
      form.resetFields();
    }
  }, [isOpen, invoice, form]);

  return (
    <Modal
      title={`Sửa hóa đơn #${invoice?.reference_code}`}
      open={isOpen}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={loading}
      width={700}
      okText="Lưu thay đổi"
      cancelText="Hủy"
      centered
      destroyOnClose
    >
      <Form 
        form={form} 
        layout="vertical" 
        onFinish={onFinish}
        className="mt-4"
      >
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
                <Button type="dashed" onClick={() => add({ item_type: InvoiceItemType.OTHER, amount: 0 })} block icon={<PlusOutlined />}>
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

export default UpdateInvoiceModal;
