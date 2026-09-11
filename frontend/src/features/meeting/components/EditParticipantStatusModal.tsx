import { useEffect } from 'react';
import { Modal, Form, Select, DatePicker, message } from 'antd';
import dayjs from 'dayjs';
import type { ParticipantResponse, ParticipantStatus, UpdateParticipantStatusPayload } from '@/features/meeting/types/meeting.types';
import { ParticipantStatus as ParticipantStatusEnum } from '@/features/meeting/types/meeting.types';

interface Props {
  open: boolean;
  participant: ParticipantResponse | null;
  onClose: () => void;
  onSubmit: (payload: UpdateParticipantStatusPayload) => Promise<void>;
  loading?: boolean;
}

const STATUS_OPTIONS: { label: string; value: ParticipantStatus; color: string }[] = [
  { label: '⚪ Chưa checkin', value: ParticipantStatusEnum.NOT_JOINED, color: 'default' },
  { label: '🟢 Đã checkin (Đúng giờ)', value: ParticipantStatusEnum.JOINED, color: 'green' },
  { label: '🔵 Trễ có phép', value: ParticipantStatusEnum.LATE_EXCUSED, color: 'blue' },
  { label: '🟠 Trễ không phép', value: ParticipantStatusEnum.LATE_UNEXCUSED, color: 'orange' },
  { label: '🟣 Vắng có phép', value: ParticipantStatusEnum.ABSENT_EXCUSED, color: 'purple' },
  { label: '🔴 Vắng không phép', value: ParticipantStatusEnum.ABSENT_UNEXCUSED, color: 'red' },
  { label: '✅ Hoàn thành (Đã checkout)', value: ParticipantStatusEnum.COMPLETED, color: 'cyan' },
];

export const EditParticipantStatusModal = ({ open, participant, onClose, onSubmit, loading }: Props) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open && participant) {
      form.setFieldsValue({
        status: participant.status,
        check_in_at: participant.check_in_at ? dayjs(participant.check_in_at) : null,
        check_out_at: participant.check_out_at ? dayjs(participant.check_out_at) : null,
      });
    } else {
      form.resetFields();
    }
  }, [open, participant, form]);

  const handleFinish = async (values: any) => {
    try {
      const payload: UpdateParticipantStatusPayload = {
        status: values.status,
        check_in_at: values.check_in_at ? values.check_in_at.toISOString() : null,
        check_out_at: values.check_out_at ? values.check_out_at.toISOString() : null,
      };
      await onSubmit(payload);
      message.success('Cập nhật trạng thái thành viên thành công');
      onClose();
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Có lỗi xảy ra khi cập nhật');
    }
  };

  return (
    <Modal
      title={`Sửa trạng thái tham gia — ${participant?.user_name || `User #${participant?.user_id}`}`}
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      okText="Lưu thay đổi"
      cancelText="Hủy"
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={handleFinish} className="mt-4">
        <Form.Item
          name="status"
          label="Trạng thái tham gia"
          rules={[{ required: true, message: 'Vui lòng chọn trạng thái' }]}
        >
          <Select placeholder="Chọn trạng thái">
            {STATUS_OPTIONS.map((opt) => (
              <Select.Option key={opt.value} value={opt.value}>
                {opt.label}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="check_in_at" label="Thời gian Check-in (Tùy chọn)">
          <DatePicker showTime format="DD/MM/YYYY HH:mm:ss" className="w-full" placeholder="Chọn thời gian checkin" />
        </Form.Item>

        <Form.Item name="check_out_at" label="Thời gian Check-out (Tùy chọn)">
          <DatePicker showTime format="DD/MM/YYYY HH:mm:ss" className="w-full" placeholder="Chọn thời gian checkout" />
        </Form.Item>
      </Form>
    </Modal>
  );
};
