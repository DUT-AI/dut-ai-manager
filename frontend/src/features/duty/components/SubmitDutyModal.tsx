import React, { useState, useEffect } from 'react';
import { Modal, Form, Checkbox, Input, Upload, Button, message, Alert, Spin } from 'antd';
import { InboxOutlined, CheckSquareOutlined, CarryOutOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import dayjs from 'dayjs';
import { dutyService } from '../services/duty.service';
import type { DutyResponse, DutyChecklistItem } from '../types/duty.types';

interface SubmitDutyModalProps {
  open?: boolean;
  isOpen?: boolean;
  dutyId: number | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const SubmitDutyModal: React.FC<SubmitDutyModalProps> = ({
  open,
  isOpen,
  dutyId,
  onClose,
  onSuccess,
}) => {
  const isModalOpen = open ?? isOpen ?? false;

  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDuty, setLoadingDuty] = useState(false);
  const [dutyDetail, setDutyDetail] = useState<DutyResponse | null>(null);
  const [checklist, setChecklist] = useState<DutyChecklistItem[]>([]);

  // Lấy dữ liệu thực tế của ca trực khi mở modal
  useEffect(() => {
    if (isModalOpen && dutyId) {
      const fetchDuty = async () => {
        try {
          setLoadingDuty(true);
          const res = await dutyService.getDutyById(dutyId);
          if (res.data) {
            setDutyDetail(res.data);
            if (res.data.checklist && res.data.checklist.length > 0) {
              setChecklist(res.data.checklist);
            } else {
              setChecklist([
                { id: '1', title: '🧹 Quét sạch sàn phòng', checked: true },
                { id: '2', title: '🪑 Lau bàn học & ghế', checked: true },
                { id: '3', title: '💨 Lau sạch quạt', checked: false },
                { id: '4', title: '🗄️ Sắp xếp & lau tủ', checked: false },
                { id: '5', title: '🪟 Lau cửa kính & cửa ra vào', checked: false },
              ]);
            }
          }
        } catch {
          // Fallback checklist mặc định nếu lỗi mạng
          setChecklist([
            { id: '1', title: '🧹 Quét sạch sàn phòng', checked: true },
            { id: '2', title: '🪑 Lau bàn học & ghế', checked: true },
            { id: '3', title: '💨 Lau sạch quạt', checked: false },
            { id: '4', title: '🗄️ Sắp xếp & lau tủ', checked: false },
            { id: '5', title: '🪟 Lau cửa kính & cửa ra vào', checked: false },
          ]);
        } finally {
          setLoadingDuty(false);
        }
      };

      fetchDuty();
      form.resetFields();
      setFileList([]);
    } else {
      setDutyDetail(null);
      setChecklist([]);
      setFileList([]);
    }
  }, [isModalOpen, dutyId, form]);

  const handleToggleChecklist = (id: string, checked: boolean) => {
    setChecklist(
      checklist.map((it) => (it.id === id ? { ...it, checked } : it))
    );
  };

  const handleSubmit = async (values: any) => {
    if (!dutyId) return;

    if (fileList.length === 0) {
      message.error('Vui lòng tải lên ít nhất 1 ảnh minh chứng thành phẩm');
      return;
    }

    const hasChecked = checklist.some((it) => it.checked);
    if (!hasChecked) {
      message.error('Vui lòng tích chọn ít nhất 1 đầu việc trực nhật đã hoàn thành');
      return;
    }

    try {
      setSubmitting(true);
      const formData = new FormData();

      // Gửi mảng checklist nội dung trực thực tế dạng JSON
      formData.append('checklist', JSON.stringify(checklist));

      if (values.note) {
        formData.append('note', values.note.trim());
      }

      fileList.forEach((file) => {
        if (file.originFileObj) {
          formData.append('files', file.originFileObj);
        }
      });

      await dutyService.submitEvidence(dutyId, formData);
      message.success('Đã nộp minh chứng trực nhật thành công, đang chờ Admin/HR duyệt!');
      form.resetFields();
      setFileList([]);
      onSuccess();
      onClose();
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Nộp minh chứng thất bại';
      message.error(errMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2 text-base font-semibold text-gray-800">
          <CarryOutOutlined className="text-blue-600" />
          <span>Nộp Minh Chứng Hoàn Thành Trực Nhật</span>
        </div>
      }
      open={isModalOpen}
      onCancel={onClose}
      footer={null}
      destroyOnClose
      width={600}
    >
      {loadingDuty ? (
        <div className="py-12 text-center">
          <Spin tip="Đang tải thông tin ca trực..." />
        </div>
      ) : (
        <>
          {dutyDetail && (
            <div className="mb-4 p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-xs space-y-1">
              <div>
                <span className="font-semibold text-blue-900">Nhóm trực: </span>
                <span className="text-blue-800">{dutyDetail.team_name || `Nhóm ID: ${dutyDetail.team_id}`}</span>
              </div>
              <div>
                <span className="font-semibold text-blue-900">Ngày trực: </span>
                <span className="text-blue-800">{dayjs(dutyDetail.duty_date).format('DD/MM/YYYY')}</span>
              </div>
              {dutyDetail.note && (
                <div>
                  <span className="font-semibold text-blue-900">Yêu cầu từ Admin/HR: </span>
                  <span className="text-gray-700 italic">"{dutyDetail.note}"</span>
                </div>
              )}
            </div>
          )}

          <Alert
            type="info"
            showIcon
            className="mb-4 text-xs"
            message="Quy định nghiệm thu trực nhật"
            description="Chỉ cần 1 bạn đại diện nhóm nộp thành công là cả nhóm được ghi nhận hoàn thành. Vui lòng tick chọn các đầu việc thực tế đã hoàn thành và tải lên ảnh chụp thành phẩm."
          />

          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            {/* Hiển thị đầu việc thực tế của ca trực */}
            <div className="mb-4">
              <div className="flex items-center gap-1.5 font-medium text-gray-800 text-sm mb-2">
                <CheckSquareOutlined className="text-indigo-600" />
                <span>Đầu việc đã thực hiện (Tick chọn ít nhất 1 việc):</span>
              </div>
              <div className="space-y-1.5 p-3 bg-gray-50 rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
                {checklist.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center p-1.5 bg-white rounded border border-gray-100"
                  >
                    <Checkbox
                      checked={item.checked}
                      onChange={(e) => handleToggleChecklist(item.id, e.target.checked)}
                      className="text-xs font-medium text-gray-700"
                    >
                      <span className={item.checked ? 'text-gray-900 font-semibold' : 'text-gray-400'}>
                        {item.title}
                      </span>
                    </Checkbox>
                  </div>
                ))}

                {checklist.length === 0 && (
                  <div className="text-center py-2 text-xs text-gray-400">
                    Chưa có đầu việc được cấu hình cho ca trực này.
                  </div>
                )}
              </div>
            </div>

            <Form.Item
              label="Ghi chú chi tiết:"
              name="note"
            >
              <Input.TextArea
                rows={3}
                placeholder="Ví dụ: Đã quét dọn và sắp xếp lại toàn bộ bàn ghế phòng Lab, đổ rác sạch sẽ..."
              />
            </Form.Item>

            <Form.Item label="Ảnh chụp thành phẩm thực tế (Tối thiểu 1 ảnh):" required>
              <Upload.Dragger
                multiple
                listType="picture"
                fileList={fileList}
                beforeUpload={() => false}
                onChange={({ fileList }) => setFileList(fileList)}
                accept="image/*"
                maxCount={5}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ color: '#2b6cb0', fontSize: 36 }} />
                </p>
                <p className="ant-upload-text">Nhấp hoặc kéo thả ảnh chụp thành phẩm vào đây</p>
                <p className="ant-upload-hint">Hỗ trợ JPG, PNG, WEBP (Tối đa 5 ảnh)</p>
              </Upload.Dragger>
            </Form.Item>

            <div className="flex justify-end gap-2 mt-6">
              <Button onClick={onClose} disabled={submitting}>
                Hủy
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={submitting}
                className="bg-blue-600 hover:bg-blue-500"
              >
                Xác nhận hoàn thành & Gửi duyệt
              </Button>
            </div>
          </Form>
        </>
      )}
    </Modal>
  );
};
