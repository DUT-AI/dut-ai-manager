import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  Form,
  Checkbox,
  Input,
  Upload,
  Button,
  message,
  Alert,
  Spin,
  Tag,
  Steps,
  Grid,
  Card,
  Tooltip,
  Typography,
} from 'antd';
import {
  InboxOutlined,
  CheckSquareOutlined,
  CarryOutOutlined,
  UserOutlined,
  RightOutlined,
  LeftOutlined,
  CameraOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import dayjs from 'dayjs';
import { useAuth } from '@/features/auth/context/AuthContext';
import { dutyService } from '../services/duty.service';
import type { DutyResponse, DutyChecklistItem } from '../types/duty.types';

const { useBreakpoint } = Grid;
const { Text } = Typography;

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
  const screens = useBreakpoint();
  const { user } = useAuth();

  // Phát hiện giao diện mobile (màn hình < 768px)
  const isMobile = screens.md === false || (typeof window !== 'undefined' && window.innerWidth < 768);

  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDuty, setLoadingDuty] = useState(false);
  const [dutyDetail, setDutyDetail] = useState<DutyResponse | null>(null);
  const [checklist, setChecklist] = useState<DutyChecklistItem[]>([]);

  // Stage dành riêng cho giao diện điện thoại (0: Điền việc & ghi chú, 1: Tải ảnh minh chứng)
  const [currentStep, setCurrentStep] = useState<number>(0);

  // Lấy dữ liệu thực tế của ca trực khi mở modal
  useEffect(() => {
    if (isModalOpen && dutyId) {
      setCurrentStep(0);
      const fetchDuty = async () => {
        try {
          setLoadingDuty(true);
          const res = await dutyService.getDutyById(dutyId);
          if (res.data) {
            setDutyDetail(res.data);
            const fetchedChecklist = res.data.checklist || [];

            // Tự động tìm nhiệm vụ được phân công của người đang đăng nhập
            const updatedChecklist = fetchedChecklist.map((item) => {
              const isMine = user && item.assignee_id === user.id;
              // Nếu đầu việc này bị REJECTED (Chưa đạt), reset checked = false để bạn đó tick lại sau khi vệ sinh lại
              const isRejectedTask = item.status === 'REJECTED';
              return {
                ...item,
                // Mặc định tự động tick việc của mình (nếu chưa tick và không bị rejected)
                checked: isRejectedTask ? false : (item.checked || Boolean(isMine)),
              };
            });

            setChecklist(
              updatedChecklist.length > 0
                ? updatedChecklist
                : [
                  { id: '1', title: 'Lau kính', checked: true },
                  { id: '2', title: 'Quạt + Đổ rác', checked: false },
                  { id: '3', title: 'Quét nhà', checked: false },
                  { id: '4', title: 'Lau bàn', checked: false },
                  { id: '5', title: 'Xếp dép', checked: false },
                ]
            );
          }
        } catch {
          setChecklist([
            { id: '1', title: 'Lau kính', checked: true },
            { id: '2', title: 'Quạt + Đổ rác', checked: false },
            { id: '3', title: 'Quét nhà', checked: false },
            { id: '4', title: 'Lau bàn', checked: false },
            { id: '5', title: 'Xếp dép', checked: false },
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
      setCurrentStep(0);
    }
  }, [isModalOpen, dutyId, form, user]);

  // Kiểm tra nhiệm vụ của cá nhân người đang đăng nhập
  const myAssignedTasks = useMemo(() => {
    if (!user || checklist.length === 0) return [];
    return checklist.filter((item) => item.assignee_id === user.id);
  }, [checklist, user]);

  const handleToggleChecklist = (id: string, checked: boolean) => {
    setChecklist(
      checklist.map((it) => (it.id === id ? { ...it, checked } : it))
    );
  };

  // Xác thực bước 1 trên Mobile trước khi Next sang bước 2
  const handleNextStep = () => {
    const hasChecked = checklist.some((it) => it.checked);
    if (!hasChecked) {
      message.warning('Vui lòng tick chọn ít nhất 1 đầu việc bạn đã thực hiện');
      return;
    }
    setCurrentStep(1);
  };

  const handleSubmit = async (values: any) => {
    if (!dutyId) return;

    if (fileList.length === 0) {
      message.error('Vui lòng tải lên ít nhất 1 ảnh minh chứng thành phẩm');
      if (isMobile) setCurrentStep(1);
      return;
    }

    const checkedTasks = checklist.filter((it) => it.checked);
    if (checkedTasks.length === 0) {
      message.error('Vui lòng tick chọn ít nhất 1 đầu việc trực nhật đã hoàn thành');
      if (isMobile) setCurrentStep(0);
      return;
    }

    // Quy định: 1 bạn nộp cho nhiều bạn thì số lượng ảnh phải tương đương số việc được tick
    if (fileList.length < checkedTasks.length) {
      message.error(
        `Bạn đã chọn ${checkedTasks.length} đầu việc nhưng mới tải lên ${fileList.length} ảnh. Vui lòng tải tối thiểu ${checkedTasks.length} ảnh chụp tương ứng cho từng việc!`
      );
      if (isMobile) setCurrentStep(1);
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
          <CarryOutOutlined className="text-indigo-600 text-lg" />
          <span>Nộp Minh Chứng Trực Nhật</span>
        </div>
      }
      open={isModalOpen}
      onCancel={onClose}
      footer={null}
      destroyOnClose
      width={isMobile ? '95vw' : 860}
      className="top-6"
    >
      {loadingDuty ? (
        <div className="py-12 text-center">
          <Spin tip="Đang tải thông tin ca trực..." />
        </div>
      ) : (
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {/* Thông tin ca trực & Nhiệm vụ cá nhân */}
          {dutyDetail && (
            <div className="mb-3.5 p-3 bg-indigo-50/70 border border-indigo-100 rounded-xl text-xs flex flex-wrap justify-between items-center gap-2">
              <div className="space-y-0.5">
                <div>
                  <span className="font-semibold text-indigo-900">👥 Nhóm trực: </span>
                  <span className="text-indigo-800 font-medium">
                    {dutyDetail.team_name || `Nhóm ID: ${dutyDetail.team_id}`}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-indigo-900">📅 Ngày trực: </span>
                  <span className="text-indigo-800 font-medium">
                    {dayjs(dutyDetail.duty_date).format('DD/MM/YYYY')}
                  </span>
                </div>
              </div>

              {/* Tag nhiệm vụ của cá nhân */}
              {myAssignedTasks.length > 0 ? (
                <div className="bg-white/90 border border-indigo-200 px-3 py-1.5 rounded-lg shadow-sm">
                  <span className="text-gray-500 text-[11px] block">Nhiệm vụ của bạn:</span>
                  <span className="font-bold text-indigo-700 text-xs">
                    {myAssignedTasks.map((t) => t.title).join(', ')}
                  </span>
                </div>
              ) : (
                <Tag color="blue" className="m-0 font-medium text-xs">
                  Mỗi bạn tự nộp ảnh việc của mình
                </Tag>
              )}
            </div>
          )}

          {/* Stepper dành cho giao diện Điện thoại */}
          {isMobile && (
            <div className="mb-4">
              <Steps
                size="small"
                current={currentStep}
                items={[
                  { title: 'Chọn việc & Ghi chú' },
                  { title: 'Chụp ảnh minh chứng' },
                ]}
              />
            </div>
          )}

          {/* Bố cục nội dung: 2 Cột trên Desktop, 2 Stage trên Mobile */}
          <div className={isMobile ? 'block' : 'grid grid-cols-2 gap-5'}>
            {/* CỘT 1 / STAGE 1: Đầu việc & Ghi chú */}
            {(!isMobile || currentStep === 0) && (
              <div className="flex flex-col justify-between space-y-3">
                <div>
                  <div className="flex items-center justify-between font-medium text-gray-800 text-sm mb-2">
                    <span className="flex items-center gap-1.5">
                      <CheckSquareOutlined className="text-indigo-600" />
                      <span>Đầu việc bạn phụ trách:</span>
                    </span>
                    <Text type="secondary" className="text-xs">
                      (Tick việc đã làm)
                    </Text>
                  </div>

                  {/* Danh sách checklist kèm tên người phụ trách */}
                  <div className="space-y-1.5 p-2.5 bg-gray-50/80 rounded-xl border border-gray-200 max-h-[220px] overflow-y-auto">
                    {checklist.map((item) => {
                      const isMyTask = user && item.assignee_id === user.id;
                      return (
                        <div
                          key={item.id}
                          className={`flex items-center justify-between p-2 rounded-lg border transition-all ${isMyTask
                            ? 'bg-indigo-50/90 border-indigo-200 shadow-sm'
                            : 'bg-white border-gray-100 hover:border-gray-200'
                            }`}
                        >
                          <Checkbox
                            checked={item.checked}
                            onChange={(e) => handleToggleChecklist(item.id, e.target.checked)}
                            className="text-xs font-medium text-gray-800 flex-1 truncate"
                          >
                            <span className={item.checked ? 'font-semibold text-gray-900' : 'text-gray-500'}>
                              {item.title}
                            </span>
                          </Checkbox>

                          {/* Tag hiển thị người được phân công */}
                          {item.assignee_name && (
                            <Tag
                              color={isMyTask ? 'purple' : 'default'}
                              className="text-[11px] m-0 font-medium flex-shrink-0"
                            >
                              👤 {item.assignee_name} {isMyTask ? '(Bạn)' : ''}
                            </Tag>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Ghi chú chi tiết */}
                <Form.Item
                  label={<span className="text-xs font-semibold text-gray-700">Ghi chú chi tiết (nếu có):</span>}
                  name="note"
                  className="mb-1"
                >
                  <Input.TextArea
                    rows={isMobile ? 2 : 3}
                    placeholder="Ví dụ: Đã lau sạch cửa kính tầng 2, quét và gom rác vào thùng..."
                    className="rounded-lg text-xs"
                  />
                </Form.Item>

                {/* Nút Tiếp tục trên Mobile */}
                {isMobile && (
                  <Button
                    type="primary"
                    block
                    onClick={handleNextStep}
                    icon={<RightOutlined />}
                    className="bg-indigo-600 hover:bg-indigo-500 mt-2 font-semibold h-9 rounded-lg"
                  >
                    Tiếp theo: Tải ảnh minh chứng
                  </Button>
                )}
              </div>
            )}

            {/* CỘT 2 / STAGE 2: Upload ảnh & Quy định nghiệm thu */}
            {(!isMobile || currentStep === 1) && (
              <div className="flex flex-col justify-between space-y-3">
                <Alert
                  type="info"
                  showIcon
                  className="text-xs rounded-xl"
                  message="Linh hoạt nộp minh chứng trực nhật"
                  description="Mỗi bạn có thể tự nộp phần của mình (nộp nhiều lần không bị mất), hoặc 1 bạn có thể nộp thay cho cả nhóm. Lưu ý: Số lượng ảnh tải lên phải tương đương với số đầu việc đã tick chọn."
                />

                <Form.Item
                  label={
                    <span className="text-xs font-semibold text-gray-800 flex items-center gap-1">
                      <CameraOutlined className="text-indigo-600" />
                      <span>Ảnh chụp thành phẩm việc của bạn (Tối thiểu 1 ảnh):</span>
                    </span>
                  }
                  required
                  className="mb-1"
                >
                  <Upload.Dragger
                    multiple
                    listType="picture"
                    fileList={fileList}
                    beforeUpload={() => false}
                    onChange={({ fileList }) => setFileList(fileList)}
                    accept="image/*"
                    maxCount={5}
                    className="rounded-xl border-dashed hover:border-indigo-400"
                  >
                    <p className="ant-upload-drag-icon !mb-1">
                      <InboxOutlined style={{ color: '#4f46e5', fontSize: 32 }} />
                    </p>
                    <p className="ant-upload-text text-xs font-medium !mb-0.5">
                      Nhấp hoặc kéo thả ảnh chụp thành phẩm vào đây
                    </p>
                    <p className="ant-upload-hint text-[11px] text-gray-400">
                      Hỗ trợ chụp từ điện thoại hoặc tải ảnh JPG, PNG, WEBP (Tối đa 5 ảnh)
                    </p>
                  </Upload.Dragger>
                </Form.Item>

                {/* Nhóm nút bấm xác nhận */}
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
                  {isMobile && (
                    <Button
                      onClick={() => setCurrentStep(0)}
                      icon={<LeftOutlined />}
                      className="rounded-lg"
                    >
                      Quay lại
                    </Button>
                  )}
                  <Button onClick={onClose} disabled={submitting} className="rounded-lg">
                    Hủy
                  </Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={submitting}
                    icon={<CheckCircleOutlined />}
                    className="bg-indigo-600 hover:bg-indigo-500 font-semibold rounded-lg px-4"
                  >
                    Nộp minh chứng
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Form>
      )}
    </Modal>
  );
};
