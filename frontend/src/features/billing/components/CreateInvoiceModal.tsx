import { Modal, Form, Select, Input, Divider, Space, InputNumber, Button, DatePicker, type FormInstance } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { InvoiceItemType } from '@/features/billing/types/billing.types';
import type { UserResponse } from '@/features/users/types/user.types';
import { useTeams } from '@/features/teams/hooks/useTeams';
import type { CreateInvoiceFormValues } from '@/features/billing/types/billing.types';

const { Option } = Select;

interface CreateInvoiceModalProps {
  isOpen: boolean;
  onCancel: () => void;
  onFinish: (values: CreateInvoiceFormValues) => void;
  loading: boolean;
  users: UserResponse[];
  form: FormInstance;
}

const CreateInvoiceModal = ({
  isOpen,
  onCancel,
  onFinish,
  loading,
  users,
  form
}: CreateInvoiceModalProps) => {
  const { data: teams = [], isLoading: isLoadingTeams } = useTeams();
  const selectedTeamId = Form.useWatch('team_id', form);
  const selectedUserIds: number[] = Form.useWatch('user_ids', form) || [];
  const currentTeam = (teams || []).find(t => t.id === selectedTeamId);
  const teamMemberIds = new Set((currentTeam?.members || []).map(m => m.user_id));
  const teamMembers = (currentTeam?.members || []).map(m => ({ id: m.user_id, name: m.user_name, email: m.user_email }));
  const otherUsers = (users || []).filter(u => !teamMemberIds.has(u.id));

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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Form.Item
            name="team_id"
            label="Gán cho Nhóm / Quỹ (Bắt buộc)"
            rules={[{ required: true, message: 'Vui lòng chọn nhóm' }]}
          >
            <Select
              showSearch
              placeholder="Chọn nhóm từ danh sách"
              loading={isLoadingTeams}
              optionFilterProp="children"
            >
              {(teams || []).map(t => (
                <Option key={t.id} value={t.id}>{t.team_name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="billing_period"
            label="Kỳ hóa đơn (Tháng/Năm)"
            rules={[{ required: true, message: 'Vui lòng chọn kỳ hóa đơn' }]}
          >
            <DatePicker picker="month" format="MM/YYYY" placeholder="Chọn tháng/năm" style={{ width: '100%' }} />
          </Form.Item>
        </div>

        <Form.Item
          name="user_ids"
          label={
            <div className="flex justify-between items-center w-full">
              <span>
                Chọn thành viên (Có thể chọn nhiều){' '}
                {selectedUserIds.length > 0 && (
                  <span className="text-xs font-semibold text-indigo-600">
                    ({selectedUserIds.length} người)
                  </span>
                )}
              </span>
              <Space size="middle">
                {selectedTeamId && currentTeam && (currentTeam.members?.length ?? 0) > 0 && (
                  <Button
                    type="link"
                    size="small"
                    className="p-0 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                    onClick={() => {
                      const memberIds = (currentTeam.members || []).map(m => m.user_id);
                      form.setFieldsValue({ user_ids: memberIds });
                    }}
                  >
                    ⚡ Chọn cả team ({currentTeam.members.length})
                  </Button>
                )}
                {selectedUserIds.length > 0 && (
                  <Button
                    type="link"
                    size="small"
                    className="p-0 text-xs text-red-500 hover:text-red-700"
                    onClick={() => form.setFieldsValue({ user_ids: [] })}
                  >
                    ✕ Bỏ chọn tất cả
                  </Button>
                )}
                {users.length > 0 && selectedUserIds.length === 0 && (
                  <Button
                    type="link"
                    size="small"
                    className="p-0 text-xs text-gray-500 hover:text-gray-700"
                    onClick={() => form.setFieldsValue({ user_ids: users.map(u => u.id) })}
                  >
                    Chọn tất cả mọi người
                  </Button>
                )}
              </Space>
            </div>
          }
          rules={[{ required: true, message: 'Vui lòng chọn ít nhất 1 thành viên' }]}
        >
          <Select
            mode="multiple"
            allowClear
            showSearch
            placeholder="Tìm kiếm và chọn các thành viên (hoặc bấm 'Chọn cả team' ở trên)"
            optionFilterProp="children"
            style={{ width: '100%' }}
          >
            {currentTeam && teamMembers.length > 0 && (
              <Select.OptGroup label={`Thành viên nhóm ${currentTeam.team_name} (${teamMembers.length})`}>
                {teamMembers.map(u => (
                  <Option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </Option>
                ))}
              </Select.OptGroup>
            )}
            {otherUsers.length > 0 && (
              <Select.OptGroup label={currentTeam ? `Các thành viên khác (${otherUsers.length})` : 'Tất cả thành viên'}>
                {otherUsers.map(u => (
                  <Option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </Option>
                ))}
              </Select.OptGroup>
            )}
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
                    <InputNumber<number>
                      min={0}
                      formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => Number(value?.replace(/\$\s?|(,*)/g, '') || 0)}
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
