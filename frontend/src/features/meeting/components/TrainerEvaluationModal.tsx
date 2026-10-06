import React, { useEffect } from 'react';
import { Modal, Form, Rate, Input, message, Typography, Space, Divider, Select, Avatar } from 'antd';
import { UserOutlined, StarFilled } from '@ant-design/icons';
import { meetingService } from '../services/meeting.service';
import { useQueryClient } from '@tanstack/react-query';
import type { ParticipantResponse, EvaluationResponse } from '../types/meeting.types';

const { TextArea } = Input;
const { Text } = Typography;

interface Props {
  open: boolean;
  meetingId: number;
  trainee: ParticipantResponse | null;
  existingEvaluation?: EvaluationResponse | null;
  participants?: ParticipantResponse[];
  onSelectTrainee?: (trainee: ParticipantResponse) => void;
  onSuccess: () => void;
  onClose?: () => void;
  onCancel?: () => void;
}

const TRAINER_CRITERIA = [
  {
    code: 'ATTENDANCE_CONDUCT',
    label: 'Chuyên cần & Tác phong',
    desc: 'Đúng giờ, tuân thủ nội quy và kỷ luật lớp học',
  },
  {
    code: 'INTERACTION_CONTRIBUTION',
    label: 'Mức độ Tương tác & Đóng góp',
    desc: 'Tích cực phát biểu, đặt câu hỏi, thảo luận sôi nổi',
  },
  {
    code: 'ABSORPTION_COMPREHENSION',
    label: 'Mức độ Tiếp thu & Hiểu bài',
    desc: 'Nắm bắt tốt kiến thức cốt lõi truyền đạt trong buổi học',
  },
  {
    code: 'PRE_CLASS_PREPARATION',
    label: 'Mức độ Chuẩn bị bài trước buổi học',
    desc: 'Đọc trước tài liệu, chuẩn bị bài tập / môi trường trước khi lên lớp',
  },
];

export const TrainerEvaluationModal: React.FC<Props> = ({
  open,
  meetingId,
  trainee,
  existingEvaluation,
  participants = [],
  onSelectTrainee,
  onSuccess,
  onClose,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = React.useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (open) {
      if (existingEvaluation && existingEvaluation.scores?.length > 0) {
        const vals: Record<string, any> = {
          feedback_text: existingEvaluation.feedback_text || '',
        };
        existingEvaluation.scores.forEach((s) => {
          vals[s.criteria_code] = s.score;
        });
        form.setFieldsValue(vals);
      } else {
        form.resetFields();
      }
    }
  }, [open, trainee?.user_id, existingEvaluation]);

  const handleClose = () => {
    if (onClose) onClose();
    if (onCancel) onCancel();
  };

  const handleFinish = async (values: any) => {
    if (!trainee) return;
    setSubmitting(true);
    try {
      const scores = TRAINER_CRITERIA.map((c) => ({
        criteria_code: c.code,
        score: values[c.code] || 5,
      }));

      const res = await meetingService.submitTrainerEvaluation(meetingId, {
        target_user_id: trainee.user_id,
        scores,
        feedback_text: values.feedback_text,
      });

      if (res.is_success) {
        message.success(
          existingEvaluation
            ? `Đã cập nhật đánh giá cho học viên ${trainee.user_name || ''}`
            : `Đã lưu đánh giá cho học viên ${trainee.user_name || ''}`
        );
        queryClient.invalidateQueries({ queryKey: ['meetings', meetingId] });
        form.resetFields();
        onSuccess();
      } else {
        message.error(res.message || 'Lỗi khi gửi đánh giá');
      }
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Không thể gửi đánh giá');
    } finally {
      setSubmitting(false);
    }
  };

  const initialValues = TRAINER_CRITERIA.reduce((acc, c) => {
    acc[c.code] = 5;
    return acc;
  }, {} as Record<string, number>);

  return (
    <Modal
      title={
        <Space>
          <StarFilled style={{ color: '#faad14' }} />
          <span>
            {existingEvaluation ? 'Cập nhật Đánh giá Học viên (Trainer)' : 'Đánh giá Học viên (Trainer)'}
          </span>
        </Space>
      }
      open={open}
      onCancel={handleClose}
      onOk={form.submit}
      confirmLoading={submitting}
      destroyOnClose
      width={560}
    >
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary" className="block text-xs uppercase font-semibold text-gray-500 mb-1.5">
          Học viên được đánh giá:
        </Text>
        {participants && participants.length > 0 && onSelectTrainee ? (
          <Select
            value={trainee?.user_id}
            onChange={(userId) => {
              const selected = participants.find((p) => p.user_id === userId);
              if (selected) onSelectTrainee(selected);
            }}
            className="w-full"
            size="large"
            placeholder="Chọn học viên..."
            options={participants.map((p) => ({
              value: p.user_id,
              label: (
                <div className="flex items-center gap-2">
                  <Avatar src={p.user_avatar_url} icon={<UserOutlined />} size="small" />
                  <span className="font-medium">{p.user_name || `User #${p.user_id}`}</span>
                  {p.status === 'ABSENT_EXCUSED' || p.status === 'ABSENT_UNEXCUSED' ? (
                    <span className="text-xs text-red-500">(Vắng mặt)</span>
                  ) : null}
                </div>
              ),
            }))}
          />
        ) : (
          <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg border border-gray-100">
            <Avatar src={trainee?.user_avatar_url} icon={<UserOutlined />} size="default" />
            <Text strong style={{ fontSize: 16 }}>
              {trainee?.user_name || `User #${trainee?.user_id}`}
            </Text>
          </div>
        )}
      </div>
      <Divider style={{ margin: '12px 0' }} />

      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleFinish}
      >
        {TRAINER_CRITERIA.map((c) => (
          <Form.Item
            key={c.code}
            name={c.code}
            label={
              <div>
                <Text strong>{c.label}</Text>
                <div style={{ fontSize: 12, color: '#8c8c8c' }}>{c.desc}</div>
              </div>
            }
            rules={[{ required: true, message: 'Vui lòng chấm điểm tiêu chí này!' }]}
          >
            <Rate allowClear={false} />
          </Form.Item>
        ))}

        <Form.Item name="feedback_text" label={<Text strong>Nhận xét / Lời khuyên</Text>}>
          <TextArea
            rows={3}
            placeholder="Ghi nhận sự tiến bộ hoặc điểm cần cải thiện của học viên..."
            maxLength={2000}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
