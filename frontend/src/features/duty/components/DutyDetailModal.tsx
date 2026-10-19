import React, { useState } from 'react';
import { Modal, Tag, Descriptions, Image, Typography, Empty, Button, Space, Input, Popconfirm } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { DutyResponse } from '../types/duty.types';

const { Text } = Typography;

interface DutyDetailModalProps {
  open: boolean;
  duty: DutyResponse | null;
  canManage?: boolean;
  onClose: () => void;
  onApprove?: (dutyId: number) => void;
  onReject?: (dutyId: number, reason: string) => void;
}

export const DutyDetailModal: React.FC<DutyDetailModalProps> = ({
  open,
  duty,
  canManage,
  onClose,
  onApprove,
  onReject,
}) => {
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  if (!duty) return null;

  const handleConfirmReject = () => {
    if (onReject) {
      onReject(duty.id, rejectReason || 'Chưa đạt yêu cầu vệ sinh, vui lòng dọn dẹp lại');
      setIsRejectOpen(false);
      setRejectReason('');
      onClose();
    }
  };

  const renderStatusTag = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Tag color="success">COMPLETED</Tag>;
      case 'AWAITING_APPROVAL':
        return <Tag color="gold" className="font-semibold">AWAITING APPROVAL</Tag>;
      case 'REJECTED':
        return <Tag color="error" className="font-semibold">REJECTED</Tag>;
      case 'VIOLATED':
        return <Tag color="error">VIOLATED</Tag>;
      case 'CANCELLED':
        return <Tag color="default">CANCELLED</Tag>;
      default:
        return <Tag color="warning">PENDING</Tag>;
    }
  };

  const checklist = duty.checklist || [];

  return (
    <>
      <Modal
        title="Chi Tiết Ca Trực Nhật Lab"
        open={open}
        onCancel={onClose}
        footer={
          <div className="flex justify-between items-center w-full">
            <div>
              {canManage && duty.status === 'AWAITING_APPROVAL' && (
                <Space>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    className="!bg-emerald-600 hover:!bg-emerald-500"
                    onClick={() => {
                      onApprove?.(duty.id);
                      onClose();
                    }}
                  >
                    Duyệt đạt chuẩn
                  </Button>
                  <Button
                    danger
                    icon={<CloseCircleOutlined />}
                    onClick={() => setIsRejectOpen(true)}
                  >
                    Từ chối
                  </Button>
                </Space>
              )}
            </div>
            <Button onClick={onClose}>Đóng</Button>
          </div>
        }
        width={680}
        destroyOnClose
      >
        <Descriptions bordered column={2} size="small" className="mt-4">
          <Descriptions.Item label="Ngày trực" span={1}>
            <Text strong>{dayjs(duty.duty_date).format('DD/MM/YYYY')}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Khung giờ trực" span={1}>
            <Text strong className="text-slate-700">
              {duty.start_time
                ? `${duty.start_time.slice(0, 5)}${duty.end_time ? ` – ${duty.end_time.slice(0, 5)}` : ''}`
                : 'Chưa cài đặt giờ'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Trạng thái" span={2}>
            {renderStatusTag(duty.status)}
          </Descriptions.Item>
          <Descriptions.Item label="Nhóm phụ trách" span={2}>
            {duty.team_names && duty.team_names.length > 1 ? (
              <div className="flex flex-wrap gap-1.5 py-1">
                {duty.team_names.map((tName, idx) => (
                  <Tag key={idx} color={idx === 0 ? "blue" : "cyan"} className="font-medium text-xs px-2 py-0.5 rounded m-0">
                    👥 {tName}
                  </Tag>
                ))}
              </div>
            ) : (
              <Text strong className="text-blue-600">
                {duty.team_name || `Nhóm ID: ${Array.isArray(duty.team_id) ? duty.team_id.join(', ') : duty.team_id}`}
              </Text>
            )}
          </Descriptions.Item>
          {duty.meeting_title && (
            <Descriptions.Item label="Buổi họp gắn kèm" span={2}>
              {duty.meeting_title}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="Người nộp đại diện" span={1}>
            {duty.submitted_by_name || 'Chưa có'}
          </Descriptions.Item>
          <Descriptions.Item label="Thời điểm nộp" span={1}>
            {duty.submitted_at
              ? dayjs(duty.submitted_at.replace(/Z|[+-]\d{2}:\d{2}$/, '')).format('HH:mm:ss DD/MM/YYYY')
              : 'Chưa nộp'}
          </Descriptions.Item>

          {/* Lý do từ chối nếu có */}
          {duty.rejection_reason && (
            <Descriptions.Item label="Lý do từ chối" span={2}>
              <div className="text-rose-700 bg-rose-50 border border-rose-200 p-2 rounded">
                <Text strong className="text-rose-800">⚠️ {duty.rejection_reason}</Text>
                <div className="text-xs text-rose-600 mt-1">
                  Học viên cần vệ sinh lại các khu vực trên và nộp lại trước 22h00.
                </div>
              </div>
            </Descriptions.Item>
          )}

          <Descriptions.Item label="Nội dung đầu việc" span={2}>
            {checklist.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {checklist.map((item) => (
                  <Tag
                    key={item.id}
                    color={item.checked ? 'green' : 'default'}
                    className="font-medium"
                  >
                    {item.checked ? '✅ ' : '⬜ '}
                    {item.title}
                  </Tag>
                ))}
              </div>
            ) : (
              <Text type="secondary">Chưa ghi nhận</Text>
            )}
          </Descriptions.Item>
          {duty.note && (
            <Descriptions.Item label="Ghi chú (Note)" span={2}>
              <div className="bg-gray-50 p-2 rounded text-gray-700 italic">
                "{duty.note}"
              </div>
            </Descriptions.Item>
          )}
        </Descriptions>

        <div className="mt-6">
          <Text strong className="block mb-2 text-base">
            📸 Minh chứng thành phẩm đã nộp ({duty.evidence_image_urls.length} ảnh):
          </Text>
          {duty.evidence_image_urls.length > 0 ? (
            <Image.PreviewGroup>
              <div className="grid grid-cols-3 gap-3">
                {duty.evidence_image_urls.map((url, idx) => (
                  <Image
                    key={idx}
                    src={url}
                    className="rounded-lg object-cover h-32 w-full border"
                    alt={`Thành phẩm ${idx + 1}`}
                  />
                ))}
              </div>
            </Image.PreviewGroup>
          ) : (
            <Empty description="Chưa có ảnh minh chứng nào được tải lên" />
          )}
        </div>
      </Modal>

      {/* Modal từ chối */}
      <Modal
        title="Từ chối minh chứng trực nhật"
        open={isRejectOpen}
        onOk={handleConfirmReject}
        onCancel={() => {
          setIsRejectOpen(false);
          setRejectReason('');
        }}
        okText="Xác nhận từ chối"
        cancelText="Hủy"
        okButtonProps={{ danger: true }}
      >
        <div className="py-2">
          <Text type="secondary" className="block mb-2 text-xs">
            Vui lòng nhập lý do từ chối để học viên nắm được các khu vực chưa đạt (sàn, quạt, bàn, rác...) và dọn dẹp lại trước 22h00:
          </Text>
          <Input.TextArea
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Ví dụ: Sàn nhà còn ướt và chưa quét sạch rác góc phòng..."
          />
        </div>
      </Modal>
    </>
  );
};
