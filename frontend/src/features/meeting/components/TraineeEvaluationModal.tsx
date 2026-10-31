import React, { useEffect, useState } from 'react';
import {
  Modal,
  Form,
  Rate,
  Input,
  Switch,
  message,
  Typography,
  Space,
  Divider,
  Avatar,
  Alert,
  Select,
} from 'antd';
import {
  HeartFilled,
  EyeInvisibleOutlined,
  UserOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { meetingService } from '../services/meeting.service';
import { useQueryClient } from '@tanstack/react-query';
import type { EvaluationResponse, UserRefDto } from '../types/meeting.types';

const { TextArea } = Input;
const { Text } = Typography;

interface Props {
  open: boolean;
  meetingId: number;
  trainers?: UserRefDto[];
  trainerId?: number;
  trainerName?: string;
  trainerAvatarUrl?: string | null;
  existingEvaluation?: EvaluationResponse | null;
  onSuccess: () => void;
  onClose?: () => void;
  onCancel?: () => void;
}

const TRAINEE_CRITERIA = [
  {
    code: 'CONTENT_QUALITY',
    label: 'Chất lượng Nội dung bài học',
    desc: 'Rõ ràng, thực tế, bố cục bài giảng hợp lý và dễ theo dõi',
  },
  {
    code: 'TEACHING_METHOD',
    label: 'Phương pháp Giảng dạy & Hỗ trợ',
    desc: 'Trainer truyền đạt dễ hiểu, nhiệt tình giải đáp các thắc mắc',
  },
  {
    code: 'CLASS_ATMOSPHERE',
    label: 'Không khí Lớp học & Sự tương tác',
    desc: 'Lôi cuốn, truyền cảm hứng và tạo động lực học tập tốt',
  },
  {
    code: 'PRACTICAL_VALUE',
    label: 'Giá trị Thu nhận & Tính ứng dụng',
    desc: 'Kiến thức thu nhận bổ ích, có thể ứng dụng trực tiếp vào thực tế',
  },
];

export const TraineeEvaluationModal: React.FC<Props> = ({
  open,
  meetingId,
  trainers = [],
  trainerId,
  trainerName,
  trainerAvatarUrl,
  existingEvaluation,
  onSuccess,
  onClose,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [selectedTrainerId, setSelectedTrainerId] = useState<number | undefined>(
    trainerId || trainers[0]?.id
  );
  const queryClient = useQueryClient();

  useEffect(() => {
    if (open) {
      const initialId =
        existingEvaluation?.target_user_id || trainerId || trainers[0]?.id;
      setSelectedTrainerId(initialId);

      if (existingEvaluation && existingEvaluation.scores?.length > 0) {
        const vals: Record<string, any> = {
          is_anonymous: existingEvaluation.is_anonymous ?? false,
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
  }, [open, existingEvaluation, trainerId, trainers]);

  const currentTrainer =
    trainers.find((t) => t.id === selectedTrainerId) ||
    (trainerId
      ? { id: trainerId, name: trainerName || `Trainer #${trainerId}`, avatar_url: trainerAvatarUrl }
      : null);

  const handleFinish = async (values: any) => {
    setSubmitting(true);
    try {
      const scores = TRAINEE_CRITERIA.map((c) => ({
        criteria_code: c.code,
        score: values[c.code] || 5,
      }));

      const payload: any = {
        is_anonymous: values.is_anonymous ?? false,
        scores,
        feedback_text: values.feedback_text,
      };

      if (selectedTrainerId) {
        payload.target_user_id = selectedTrainerId;
      }

      const res = await meetingService.submitTraineeEvaluation(meetingId, payload);

      if (res.is_success) {
        message.success(
          existingEvaluation
            ? 'Đã cập nhật đánh giá cho Trainer!'
            : 'Cảm ơn bạn đã gửi đánh giá cho buổi học & Trainer!'
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

  const initialValues = {
    is_anonymous: false,
    ...TRAINEE_CRITERIA.reduce((acc, c) => {
      acc[c.code] = 5;
      return acc;
    }, {} as Record<string, number>),
  };

  const handleClose = () => {
    if (onClose) onClose();
    if (onCancel) onCancel();
  };

  return (
    <Modal
      title={
        <Space>
          <HeartFilled style={{ color: '#eb2f96' }} />
          <span>
            {existingEvaluation
              ? 'Cập nhật Đánh giá Trainer (Trainee)'
              : 'Đánh giá Trainer & Buổi học (Trainee)'}
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
      {/* Chọn Trainer phụ trách */}
      {trainers.length > 1 ? (
        <div className="mb-4">
          <label className="text-xs font-semibold text-gray-500 uppercase block mb-1.5">
            Chọn Giảng viên cần đánh giá
          </label>
          <Select
            className="w-full"
            value={selectedTrainerId}
            onChange={(val) => setSelectedTrainerId(val)}
            options={trainers.map((t) => ({
              value: t.id,
              label: (
                <div className="flex items-center gap-2">
                  <Avatar src={t.avatar_url} icon={<UserOutlined />} size="small" />
                  <span>{t.name}</span>
                </div>
              ),
            }))}
          />
        </div>
      ) : (
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100 mb-4">
          <Avatar
            src={currentTrainer?.avatar_url}
            icon={<UserOutlined />}
            size={48}
            className="shadow-sm border border-amber-200"
          />
          <div>
            <div className="flex items-center gap-1">
              <CrownOutlined className="text-amber-500 text-xs" />
              <Text
                type="secondary"
                className="text-xs uppercase font-semibold text-gray-500"
              >
                Trainer phụ trách
              </Text>
            </div>
            <Text strong className="text-base text-gray-900 block">
              {currentTrainer?.name || 'Chưa xác định Trainer'}
            </Text>
          </div>
        </div>
      )}

      <Divider style={{ margin: '12px 0' }} />

      {existingEvaluation && (
        <Alert
          type="info"
          showIcon
          className="mb-4 rounded-xl border-indigo-100 bg-indigo-50/70"
          message={
            existingEvaluation.is_anonymous ? (
              <span>
                Bạn đã gửi đánh giá <strong>ẩn danh</strong> cho Trainer. Bạn có
                thể cập nhật lại điểm số hoặc nhận xét bên dưới.
              </span>
            ) : (
              <span>
                Bạn đã gửi đánh giá cho Trainer. Bạn có thể cập nhật lại điểm số
                hoặc nhận xét bên dưới.
              </span>
            )
          }
        />
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleFinish}
      >
        {TRAINEE_CRITERIA.map((c) => (
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

        <Form.Item
          name="feedback_text"
          label={<Text strong>Góp ý / Cảm nhận cho Trainer</Text>}
        >
          <TextArea
            rows={3}
            placeholder="Chia sẻ cảm nghĩ hoặc đề xuất giúp nâng cao chất lượng buổi học..."
            maxLength={2000}
            showCount
          />
        </Form.Item>

        <Form.Item
          name="is_anonymous"
          valuePropName="checked"
          label={
            <Space>
              <EyeInvisibleOutlined />
              <span>Gửi đánh giá Ẩn danh</span>
            </Space>
          }
          extra="Khi bật, Trainer sẽ không thấy tên của bạn (hiển thị: Học viên ẩn danh)."
        >
          <Switch checkedChildren="Ẩn danh" unCheckedChildren="Công khai" />
        </Form.Item>
      </Form>
    </Modal>
  );
};
