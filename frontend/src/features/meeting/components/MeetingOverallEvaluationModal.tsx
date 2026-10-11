import React, { useEffect, useState } from 'react';
import { Modal, Form, Rate, Input, message, Typography, Space, Divider, Alert } from 'antd';
import { StarFilled, CheckCircleOutlined } from '@ant-design/icons';
import { meetingService } from '../services/meeting.service';
import { useQueryClient } from '@tanstack/react-query';
import type { MeetingOverallEvaluationResponse } from '../types/meeting.types';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Props {
  open: boolean;
  meetingId: number;
  meetingTitle?: string;
  existingEvaluation?: MeetingOverallEvaluationResponse | null;
  onSuccess: () => void;
  onClose?: () => void;
  onCancel?: () => void;
}

const MEETING_OVERALL_CRITERIA = [
  {
    code: 'ATTENDANCE_CONDUCT',
    label: 'Chuyên cần & Tác phong',
    desc: 'Đúng giờ, tuân thủ nội quy và kỷ luật chung của lớp học',
  },
  {
    code: 'INTERACTION_CONTRIBUTION',
    label: 'Mức độ Tương tác & Đóng góp',
    desc: 'Tích cực phát biểu, đặt câu hỏi, thảo luận sôi nổi',
  },
  {
    code: 'ABSORPTION_COMPREHENSION',
    label: 'Mức độ Tiếp thu & Hiểu bài',
    desc: 'Mức độ nắm bắt kiến thức cốt lõi truyền đạt trong buổi học',
  },
  {
    code: 'PRE_CLASS_PREPARATION',
    label: 'Mức độ Chuẩn bị bài trước buổi học',
    desc: 'Đọc trước tài liệu, chuẩn bị bài tập / môi trường trước khi lên lớp',
  },
];

export const MeetingOverallEvaluationModal: React.FC<Props> = ({
  open,
  meetingId,
  meetingTitle,
  existingEvaluation,
  onSuccess,
  onClose,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (open) {
      if (existingEvaluation) {
        const scoresMap: Record<string, number> = {};
        existingEvaluation.scores.forEach((s) => {
          scoresMap[s.criteria_code] = s.score;
        });
        form.setFieldsValue({
          ...scoresMap,
          general_feedback: existingEvaluation.general_feedback,
        });
      } else {
        const defaultScores: Record<string, number> = {};
        MEETING_OVERALL_CRITERIA.forEach((c) => {
          defaultScores[c.code] = 5;
        });
        form.setFieldsValue({
          ...defaultScores,
          general_feedback: '',
        });
      }
    }
  }, [open, existingEvaluation, form]);

  const handleFinish = async (values: any) => {
    try {
      setSubmitting(true);
      const scores = MEETING_OVERALL_CRITERIA.map((c) => ({
        criteria_code: c.code,
        score: values[c.code] || 5,
      }));

      await meetingService.submitMeetingOverallEvaluation(meetingId, {
        scores,
        general_feedback: values.general_feedback?.trim() || undefined,
      });

      message.success(
        existingEvaluation
          ? 'Cập nhật đánh giá buổi học thành công'
          : 'Đã hoàn thành đánh giá buổi học'
      );
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['meeting-overall-evaluation', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meeting-evaluation-summary', meetingId] });
      onSuccess();
    } catch (err: any) {
      message.error(err?.response?.data?.message || 'Không thể lưu đánh giá buổi học');
    } finally {
      setSubmitting(false);
    }
  };

  const handleModalClose = () => {
    form.resetFields();
    if (onClose) onClose();
    if (onCancel) onCancel();
  };

  return (
    <Modal
      open={open}
      title={
        <Space direction="vertical" size={2}>
          <Title level={4} style={{ margin: 0 }}>
            {existingEvaluation ? 'Cập Nhật Đánh Giá Buổi Học' : 'Đánh Giá Tổng Thể Buổi Học'}
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Trainer đánh giá chung toàn bộ buổi học ({meetingTitle || `Meeting #${meetingId}`})
          </Text>
        </Space>
      }
      onCancel={handleModalClose}
      onOk={() => form.submit()}
      confirmLoading={submitting}
      okText={existingEvaluation ? 'Cập Nhật Đánh Giá' : 'Gửi Đánh Giá Buổi Học'}
      cancelText="Đóng"
      width={600}
      destroyOnClose
    >
      <Alert
        message="Đánh giá 1 - 1 cho cả Buổi học"
        description="Bạn chỉ cần thực hiện 1 phiếu đánh giá tổng thể này thay vì chấm từng học viên riêng lẻ. Kết quả sẽ được công khai cho học viên tham gia lớp."
        type="info"
        showIcon
        icon={<CheckCircleOutlined />}
        style={{ marginBottom: 20 }}
      />

      <Form form={form} layout="vertical" onFinish={handleFinish}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {MEETING_OVERALL_CRITERIA.map((criterion) => (
            <div
              key={criterion.code}
              style={{
                padding: '12px 16px',
                background: '#f8fafc',
                borderRadius: 8,
                border: '1px solid #e2e8f0',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Text strong style={{ fontSize: 14 }}>
                  {criterion.label}
                </Text>
                <Form.Item name={criterion.code} noStyle rules={[{ required: true, message: 'Vui lòng cho điểm' }]}>
                  <Rate character={<StarFilled />} style={{ color: '#f59e0b', fontSize: 18 }} />
                </Form.Item>
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {criterion.desc}
              </Text>
            </div>
          ))}
        </div>

        <Divider style={{ margin: '20px 0 16px' }} />

        <Form.Item
          name="general_feedback"
          label={<Text strong>Nhận xét chung cho cả buổi học (Tùy chọn)</Text>}
        >
          <TextArea
            rows={4}
            maxLength={2000}
            showCount
            placeholder="Chia sẻ nhận xét về tinh thần học tập, mức độ tiếp thu và các điểm cần cải thiện của buổi học..."
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
