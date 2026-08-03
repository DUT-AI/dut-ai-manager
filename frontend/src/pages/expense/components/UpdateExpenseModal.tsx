import React, { useEffect } from 'react';
import { Modal, Form, DatePicker, InputNumber, Input, Select, Radio } from 'antd';
import dayjs from 'dayjs';
import { useUsers } from '@/hooks';
import { useTeams } from '@/hooks/useTeams';
import { useUpdateExpense } from '@/hooks/useExpense';
import { ExpenseStatus, type ExpenseInvoice } from '@/types/expense.types';

interface UpdateExpenseModalProps {
  open: boolean;
  expense: ExpenseInvoice | null;
  onClose: () => void;
}

export const UpdateExpenseModal: React.FC<UpdateExpenseModalProps> = ({ open, expense, onClose }) => {
  const [form] = Form.useForm();
  const { data: usersData, isLoading: isLoadingUsers } = useUsers();
  const { data: teamsData, isLoading: isLoadingTeams } = useTeams();
  const users = usersData || [];
  const teams = teamsData || [];
  const updateExpenseMutation = useUpdateExpense();

  useEffect(() => {
    if (open && expense) {
      form.setFieldsValue({
        expense_date: dayjs(expense.expense_date),
        amount: expense.amount,
        description: expense.description,
        spender_id: expense.spender_id,
        team_id: expense.team_id,
        status: expense.status,
        note: expense.note,
      });
    }
  }, [open, expense, form]);

  const handleSubmit = async () => {
    if (!expense) return;
    try {
      const values = await form.validateFields();
      await updateExpenseMutation.mutateAsync({
        id: expense.id,
        data: {
          expense_date: values.expense_date.format('YYYY-MM-DD'),
          amount: values.amount,
          description: values.description,
          spender_id: values.spender_id,
          team_id: values.team_id,
          status: values.status,
          note: values.note,
          payment_date: values.status === ExpenseStatus.PAID ? values.expense_date.format('YYYY-MM-DD') : null,
        },
      });
      onClose();
    } catch {
      // Form validation error
    }
  };

  return (
    <Modal
      title="Cập nhật hóa đơn xuất ra"
      open={open}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={updateExpenseMutation.isPending}
      okText="Lưu thay đổi"
      cancelText="Hủy"
      width={520}
      destroyOnClose
    >
      <Form form={form} layout="vertical" className="mt-4">
        <Form.Item
          name="expense_date"
          label="Ngày tháng chi"
          rules={[{ required: true, message: 'Vui lòng chọn ngày chi' }]}
        >
          <DatePicker className="w-full" format="DD/MM/YYYY" placeholder="Chọn ngày chi" />
        </Form.Item>

        <Form.Item
          name="amount"
          label="Số tiền (VNĐ)"
          rules={[
            { required: true, message: 'Vui lòng nhập số tiền' },
            { type: 'number', min: 1000, message: 'Số tiền tối thiểu 1.000 VNĐ' },
          ]}
        >
          <InputNumber
            className="w-full"
            placeholder="Ví dụ: 500000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value?.replace(/\$\s?|(,*)/g, '') as unknown as number}
            addonAfter="VNĐ"
          />
        </Form.Item>

        <Form.Item
          name="spender_id"
          label="Người chi (Bắt buộc)"
          rules={[{ required: true, message: 'Vui lòng chọn người chi' }]}
        >
          <Select
            placeholder="Chọn người chi từ danh sách"
            loading={isLoadingUsers}
            showSearch
            optionFilterProp="label"
            options={users.map((u) => ({
              value: u.id,
              label: `${u.name} (${u.email})`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="team_id"
          label="Nhóm (Bắt buộc)"
          rules={[{ required: true, message: 'Vui lòng chọn nhóm' }]}
        >
          <Select
            placeholder="Chọn nhóm từ danh sách"
            loading={isLoadingTeams}
            showSearch
            optionFilterProp="label"
            options={teams.map((t) => ({
              value: t.id,
              label: t.team_name,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="description"
          label="Nội dung chi"
          rules={[{ required: true, message: 'Vui lòng nhập nội dung chi' }]}
        >
          <Input.TextArea rows={3} placeholder="Ví dụ: Chi phí mua Server Cloud tháng 8" />
        </Form.Item>

        <Form.Item
          name="status"
          label="Tình trạng thanh toán"
          rules={[{ required: true, message: 'Vui lòng chọn tình trạng' }]}
        >
          <Radio.Group buttonStyle="solid">
            <Radio.Button value={ExpenseStatus.UNPAID}>Chưa trả (UNPAID)</Radio.Button>
            <Radio.Button value={ExpenseStatus.PAID}>Đã trả (PAID)</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item name="note" label="Ghi chú thêm (Không bắt buộc)">
          <Input.TextArea rows={2} placeholder="Nhập ghi chú nếu có" />
        </Form.Item>
      </Form>
    </Modal>
  );
};
