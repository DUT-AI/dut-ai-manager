import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tag,
  Descriptions,
  Image,
  Typography,
  Empty,
  Button,
  Space,
  Input,
  Tooltip,
  message,
  Alert,
  Select,
  Popconfirm,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { DutyResponse, DutyChecklistItem } from '../types/duty.types';
import { dutyService } from '../services/duty.service';

const { Text } = Typography;

interface DutyDetailModalProps {
  open: boolean;
  duty: DutyResponse | null;
  canManage?: boolean;
  onClose: () => void;
  onApprove?: (dutyId: number) => void;
  onReject?: (dutyId: number, reason: string) => void;
  onRefresh?: () => void;
}

export const DutyDetailModal: React.FC<DutyDetailModalProps> = ({
  open,
  duty,
  canManage,
  onClose,
  onApprove,
  onReject,
  onRefresh,
}) => {
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [checklist, setChecklist] = useState<DutyChecklistItem[]>([]);
  const [updatingTask, setUpdatingTask] = useState(false);
  const [candidates, setCandidates] = useState<import('../types/duty.types').TeamCandidateMember[]>([]);

  // Tải danh sách thành viên của nhóm để phục vụ đổi phân công
  useEffect(() => {
    if (open && duty && canManage) {
      const primaryTeamId = Array.isArray(duty.team_id) ? duty.team_id[0] : duty.team_id;
      if (primaryTeamId) {
        dutyService.getCandidates(Number(primaryTeamId)).then((res) => {
          if (res.data?.all_members) {
            setCandidates(res.data.all_members);
          }
        }).catch(() => { });
      }
    }
  }, [open, duty, canManage]);

  // State cho Modal cảnh báo thông minh khi duyệt tất cả
  const [isConfirmAllModalOpen, setIsConfirmAllModalOpen] = useState(false);

  useEffect(() => {
    if (duty) {
      setChecklist(duty.checklist || []);
    } else {
      setChecklist([]);
    }
  }, [duty]);

  if (!duty) return null;

  const totalTasks = checklist.length;
  const checkedTasks = checklist.filter((item) => item.checked);
  const uncheckedTasks = checklist.filter((item) => !item.checked);
  const imageCount = duty.evidence_image_urls?.length || 0;

  // Ca trực đã hoàn tất hoặc bị hủy thì không cho phép duyệt lại nhiều lần
  const isFinalized = duty.status === 'COMPLETED' || duty.status === 'CANCELLED';

  // Ca trực có bị thiếu việc hoặc thiếu ảnh không?
  const isMissingWork =
    totalTasks > 0 && (checkedTasks.length < totalTasks || imageCount < totalTasks);

  const handleConfirmReject = () => {
    if (onReject) {
      onReject(duty.id, rejectReason || 'Chưa đạt yêu cầu vệ sinh, vui lòng dọn dẹp lại');
      setIsRejectOpen(false);
      setRejectReason('');
      onClose();
    }
  };

  // Đổi người phân công cho một đầu việc chưa hoàn thành
  const handleChangeAssignee = async (itemId: string, newUserId: number) => {
    if (!duty || isFinalized) return;
    const selectedMember = candidates.find((m) => m.id === newUserId);
    const updatedChecklist = checklist.map((item) =>
      item.id === itemId
        ? {
          ...item,
          assignee_id: newUserId,
          assignee_name: selectedMember ? selectedMember.name : `Thành viên #${newUserId}`,
          status: 'PENDING' as const,
        }
        : item
    );
    setChecklist(updatedChecklist);

    try {
      setUpdatingTask(true);
      await dutyService.updateDuty(duty.id, { checklist: updatedChecklist });
      message.success(`Đã đổi người phân công sang: ${selectedMember?.name || newUserId}`);
      onRefresh?.();
    } catch {
      message.error('Không thể cập nhật người phân công');
    } finally {
      setUpdatingTask(false);
    }
  };

  // Xóa bớt một đầu việc chưa hoàn thành (bạn được giao trước đó sẽ không bị tính vi phạm)
  const handleDeleteTask = async (itemId: string) => {
    if (!duty || isFinalized) return;
    const targetItem = checklist.find((i) => i.id === itemId);
    const updatedChecklist = checklist.filter((item) => item.id !== itemId);
    setChecklist(updatedChecklist);

    try {
      setUpdatingTask(true);
      await dutyService.updateDuty(duty.id, { checklist: updatedChecklist });
      message.success(`Đã xóa đầu việc "${targetItem?.title}".`);
      onRefresh?.();
    } catch {
      message.error('Không thể xóa đầu việc');
    } finally {
      setUpdatingTask(false);
    }
  };

  // Duyệt hoặc từ chối từng đầu việc / từng bạn riêng lẻ
  const handleUpdateItemStatus = async (
    itemId: string,
    status: 'APPROVED' | 'REJECTED' | 'PENDING'
  ) => {
    if (!duty || isFinalized) return;

    const targetItem = checklist.find((i) => i.id === itemId);
    // Nếu bạn này đã có cùng trạng thái thì không gọi lại
    if (targetItem?.status === status) {
      message.info('Trạng thái này đã được thiết lập');
      return;
    }

    const updatedChecklist = checklist.map((item) =>
      item.id === itemId ? { ...item, status } : item
    );
    setChecklist(updatedChecklist);

    try {
      setUpdatingTask(true);
      await dutyService.updateDuty(duty.id, {
        checklist: updatedChecklist,
      });

      const personName = targetItem?.assignee_name || 'Học viên';

      if (status === 'APPROVED') {
        message.success(`Đã đánh giá ĐẠT cho ${personName} (${targetItem?.title})`);
      } else if (status === 'REJECTED') {
        message.warning(`Đã đánh dấu CHƯA ĐẠT cho ${personName} (${targetItem?.title})`);
      }

      onRefresh?.();
    } catch {
      message.error('Không thể cập nhật trạng thái nhiệm vụ');
    } finally {
      setUpdatingTask(false);
    }
  };

  // Xử lý khi Admin nhấn "Duyệt đạt tất cả"
  const handleInitiateApproveAll = () => {
    if (isFinalized) {
      message.warning('Ca trực này đã hoàn thành nghiệm thu, không thể duyệt lại!');
      return;
    }

    if (isMissingWork) {
      // Bật modal cảnh báo xác nhận thông minh
      setIsConfirmAllModalOpen(true);
    } else {
      // Đầy đủ 100% việc và ảnh -> duyệt bình thường
      executeApproveAll(false);
    }
  };

  const executeApproveAll = async (forceApproveAllEvenUnchecked: boolean) => {
    if (!duty || isFinalized) return;

    try {
      setUpdatingTask(true);
      // Đánh dấu status cho từng item:
      const updatedChecklist = checklist.map((item) => {
        if (item.checked || forceApproveAllEvenUnchecked) {
          return { ...item, status: 'APPROVED' as const };
        } else {
          return {
            ...item,
            status: 'REJECTED' as const,
            rejection_reason: 'Không nộp minh chứng / Chưa hoàn thành trực nhật',
          };
        }
      });

      // Lưu checklist đã phân loại
      await dutyService.updateDuty(duty.id, {
        checklist: updatedChecklist,
      });

      // Gọi API approve ca trực
      await dutyService.approveDuty(duty.id);
      message.success('Đã nghiệm thu xong ca trực!');
      setIsConfirmAllModalOpen(false);
      onRefresh?.();
      onClose();
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Không thể hoàn tất duyệt ca trực');
    } finally {
      setUpdatingTask(false);
    }
  };

  const renderStatusTag = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Tag color="success">COMPLETED (HOÀN THÀNH)</Tag>;
      case 'AWAITING_APPROVAL':
        return <Tag color="gold" className="font-semibold">AWAITING APPROVAL (CHỜ DUYỆT)</Tag>;
      case 'REJECTED':
        return <Tag color="error" className="font-semibold">REJECTED (TỪ CHỐI)</Tag>;
      case 'VIOLATED':
        return <Tag color="error">VIOLATED (VI PHẠM)</Tag>;
      case 'CANCELLED':
        return <Tag color="default">CANCELLED (HỦY)</Tag>;
      default:
        return <Tag color="warning">PENDING (CHỜ TRỰC)</Tag>;
    }
  };

  return (
    <>
      <Modal
        title={
          <div className="flex items-center gap-2">
            <span className="font-bold text-gray-800">Chi Tiết Nghiệm Thu Ca Trực Nhật</span>
            {renderStatusTag(duty.status)}
          </div>
        }
        open={open}
        onCancel={onClose}
        footer={
          <div className="flex justify-between items-center w-full">
            <div>
              {canManage && !isFinalized && (
                <Space>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    className="!bg-emerald-600 hover:!bg-emerald-500 font-semibold"
                    loading={updatingTask}
                    onClick={handleInitiateApproveAll}
                  >
                    Duyệt đạt tất cả
                  </Button>
                  <Button
                    danger
                    icon={<CloseCircleOutlined />}
                    onClick={() => setIsRejectOpen(true)}
                  >
                    Từ chối cả ca
                  </Button>
                </Space>
              )}
            </div>
            <Button onClick={onClose}>Đóng</Button>
          </div>
        }
        width={980}
        destroyOnClose
        className="top-6"
      >
        {/* Banner cảnh báo nếu thiếu người trực hoặc thiếu ảnh */}
        {isMissingWork && !isFinalized && (
          <Alert
            type="warning"
            showIcon
            className="mb-3 rounded-lg text-xs"
            message={
              <span className="font-semibold">
                Ca trực này mới nộp {checkedTasks.length}/{totalTasks} đầu việc ({imageCount} ảnh). Còn{' '}
                {uncheckedTasks.length} bạn chưa nộp minh chứng!
              </span>
            }
            description="Bạn có thể duyệt riêng từng bạn bằng nút bên dưới hoặc bấm 'Duyệt đạt tất cả'."
          />
        )}

        {/* BỐ CỤC 2 CỘT MỞ RỘNG (DESKTOP) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CỘT TRÁI: THÔNG TIN CA TRỰC & PHÂN CÔNG TỪNG BẠN */}
          <div className="space-y-3">
            <Descriptions bordered column={2} size="small" className="text-xs">
              <Descriptions.Item label="Ngày trực" span={1}>
                <Text strong>{dayjs(duty.duty_date).format('DD/MM/YYYY')}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Khung giờ" span={1}>
                <Text strong className="text-slate-700">
                  {duty.start_time
                    ? `${duty.start_time.slice(0, 5)}${duty.end_time ? ` – ${duty.end_time.slice(0, 5)}` : ''}`
                    : 'Chưa cài đặt'}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Nhóm trực" span={2}>
                {duty.team_names && duty.team_names.length > 1 ? (
                  <div className="flex flex-wrap gap-1">
                    {duty.team_names.map((tName, idx) => (
                      <Tag key={idx} color={idx === 0 ? 'blue' : 'cyan'} className="text-[11px] m-0">
                        👥 {tName}
                      </Tag>
                    ))}
                  </div>
                ) : (
                  <Text strong className="text-blue-600">
                    {duty.team_name || `Nhóm ID: ${duty.team_id}`}
                  </Text>
                )}
              </Descriptions.Item>
              {duty.meeting_title && (
                <Descriptions.Item label="Buổi sinh hoạt" span={2}>
                  {duty.meeting_title}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Người nộp đại diện" span={1}>
                {duty.submitted_by_name || 'Chưa có'}
              </Descriptions.Item>
              <Descriptions.Item label="Thời điểm nộp" span={1}>
                {duty.submitted_at
                  ? dayjs(duty.submitted_at.replace(/Z|[+-]\d{2}:\d{2}$/, '')).format('HH:mm:ss DD/MM')
                  : 'Chưa nộp'}
              </Descriptions.Item>
            </Descriptions>

            {/* Lý do từ chối nếu có */}
            {duty.rejection_reason && (
              <div className="text-rose-700 bg-rose-50 border border-rose-200 p-2.5 rounded-lg text-xs">
                <Text strong className="text-rose-800">⚠️ Lý do từ chối:</Text>
                <div className="mt-1">{duty.rejection_reason}</div>
              </div>
            )}

            {/* Ghi chú của học viên */}
            {duty.note && (
              <div className="bg-gray-50 border border-gray-200 p-2.5 rounded-lg text-xs">
                <span className="font-semibold text-gray-700 block mb-0.5">📝 Ghi chú từ người nộp:</span>
                <span className="text-gray-600 italic whitespace-pre-line">{duty.note}</span>
              </div>
            )}

            {/* Nghiệm thu & Duyệt theo từng bạn */}
            <div>
              <div className="font-semibold text-gray-800 text-xs mb-1.5 flex justify-between items-center">
                <span>Phân công & Nghiệm thu từng bạn:</span>
                <span className="text-[11px] text-gray-500 font-normal">
                  ({checkedTasks.length}/{totalTasks} đã tick làm)
                </span>
              </div>

              {checklist.length > 0 ? (
                <div className="space-y-1.5 max-h-[280px] overflow-y-auto pr-1">
                  {checklist.map((item) => {
                    const isApproved = item.status === 'APPROVED';
                    const isRejected = item.status === 'REJECTED';

                    return (
                      <div
                        key={item.id}
                        className={`flex justify-between items-center p-2 rounded-lg border text-xs transition-colors ${isApproved
                          ? 'bg-emerald-50/80 border-emerald-200'
                          : isRejected
                            ? 'bg-rose-50/80 border-rose-200'
                            : 'bg-white border-gray-200'
                          }`}
                      >
                        <div className="flex-1 min-w-0 pr-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-medium text-gray-800">
                              {item.checked ? '✅ ' : '⬜ '}
                              {item.title}
                            </span>
                            {item.assignee_name && (
                              <Tag color="indigo" className="m-0 font-medium text-[11px]">
                                👤 {item.assignee_name}
                              </Tag>
                            )}
                          </div>
                          {!item.checked && (
                            <span className="text-[11px] text-amber-600 block mt-0.5">
                              • Chưa nộp minh chứng / chưa tick
                            </span>
                          )}
                        </div>

                        {/* Nút đổi người / xóa đầu việc chưa làm & nút nghiệm thu từng bạn */}
                        {canManage && !isFinalized ? (
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {isApproved ? (
                              <Tag color="success" className="m-0 font-semibold text-[10px]">
                                Đạt chuẩn
                              </Tag>
                            ) : isRejected ? (
                              <Tag color="error" className="m-0 font-semibold text-[10px]">
                                Chưa đạt
                              </Tag>
                            ) : null}

                            {/* Nếu chưa tick hoàn thành: Cho phép đổi người phụ trách hoặc xóa đầu việc */}
                            {!item.checked && (
                              <Space orientation="horizontal" size={4}>
                                {candidates.length > 0 && (
                                  <Select
                                    size="small"
                                    showSearch
                                    optionFilterProp="label"
                                    value={item.assignee_id || undefined}
                                    placeholder="Đổi bạn..."
                                    className="w-28 text-[11px]"
                                    disabled={updatingTask}
                                    onChange={(newVal) => handleChangeAssignee(item.id, newVal)}
                                    options={candidates.map((c) => ({
                                      value: c.id,
                                      label: c.name,
                                    }))}
                                  />
                                )}
                                <Popconfirm
                                  title="Xóa đầu việc này?"
                                  description="Xóa việc này thì bạn được giao sẽ không bị tính vi phạm."
                                  onConfirm={() => handleDeleteTask(item.id)}
                                  okText="Xóa"
                                  cancelText="Hủy"
                                  okButtonProps={{ danger: true, size: 'small' }}
                                  cancelButtonProps={{ size: 'small' }}
                                >
                                  <Tooltip title="Xóa đầu việc">
                                    <Button
                                      size="small"
                                      type="text"
                                      danger
                                      icon={<DeleteOutlined />}
                                      disabled={updatingTask}
                                    />
                                  </Tooltip>
                                </Popconfirm>
                              </Space>
                            )}

                            <Tooltip title={isApproved ? 'Đã duyệt đạt' : 'Duyệt đạt cho bạn này'}>
                              <Button
                                size="small"
                                type={isApproved ? 'primary' : 'default'}
                                className={isApproved ? '!bg-emerald-600' : 'text-emerald-700 hover:!border-emerald-500'}
                                icon={<CheckOutlined />}
                                disabled={updatingTask}
                                onClick={() => handleUpdateItemStatus(item.id, 'APPROVED')}
                              />
                            </Tooltip>

                            <Tooltip title={isRejected ? 'Đã từ chối' : 'Đánh dấu chưa đạt / Trốn trực'}>
                              <Button
                                size="small"
                                danger
                                type={isRejected ? 'primary' : 'default'}
                                icon={<CloseOutlined />}
                                disabled={updatingTask}
                                onClick={() => handleUpdateItemStatus(item.id, 'REJECTED')}
                              />
                            </Tooltip>
                          </div>
                        ) : (
                          <div>
                            {isApproved && <Tag color="success" className="m-0 text-[10px]">Đạt chuẩn</Tag>}
                            {isRejected && <Tag color="error" className="m-0 text-[10px]">Không đạt</Tag>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <Text type="secondary" className="text-xs">Chưa ghi nhận danh sách đầu việc</Text>
              )}
            </div>
          </div>

          {/* CỘT PHẢI: MINH CHỨNG THÀNH PHẨM (ẢNH CHỤP) */}
          <div className="flex flex-col h-full">
            <div className="font-semibold text-gray-800 text-xs mb-2 flex justify-between items-center">
              <span>📸 Ảnh chụp thành phẩm ({duty.evidence_image_urls.length} ảnh):</span>
              <span className="text-[11px] text-gray-400">Nhấp vào ảnh để phóng to</span>
            </div>

            <div className="p-2.5 bg-gray-50/80 rounded-xl border border-gray-200 flex-1 min-h-[300px] overflow-y-auto">
              {duty.evidence_image_urls.length > 0 ? (
                <Image.PreviewGroup>
                  <div className="grid grid-cols-2 gap-2.5">
                    {duty.evidence_image_urls.map((url, idx) => (
                      <div key={idx} className="relative group overflow-hidden rounded-lg border border-gray-200 bg-white">
                        <Image
                          src={url}
                          className="object-cover h-36 w-full transition-transform duration-200 group-hover:scale-105"
                          alt={`Minh chứng ${idx + 1}`}
                        />
                        <div className="text-center py-1 text-[11px] text-gray-500 font-medium bg-white/90">
                          Ảnh {idx + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                </Image.PreviewGroup>
              ) : (
                <div className="py-16 text-center">
                  <Empty description="Chưa có ảnh minh chứng nào được tải lên" />
                </div>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {/* Modal xác nhận thông minh khi Duyệt tất cả nhưng chưa đủ việc/ảnh */}
      <Modal
        title={
          <div className="flex items-center gap-2 text-amber-600">
            <ExclamationCircleOutlined className="text-xl" />
            <span className="font-bold text-gray-800">Xác nhận nghiệm thu ca trực chưa đủ minh chứng</span>
          </div>
        }
        open={isConfirmAllModalOpen}
        onCancel={() => setIsConfirmAllModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <div className="py-2 space-y-3">
          <Alert
            type="warning"
            showIcon
            message="Phát hiện nhiệm vụ chưa hoàn tất"
            description={
              <div className="text-xs space-y-1 mt-1">
                <div>
                  • Tổng đầu việc: <strong>{totalTasks} việc</strong>
                </div>
                <div>
                  • Đã tick nộp minh chứng: <strong>{checkedTasks.length} việc</strong>
                </div>
                <div className="text-rose-600 font-semibold">
                  • Chưa nộp minh chứng: {uncheckedTasks.length} bạn (
                  {uncheckedTasks.map((t) => t.assignee_name || t.title).join(', ')})
                </div>
              </div>
            }
          />

          <div className="text-xs text-gray-600 font-medium">
            Vui lòng chọn phương án nghiệm thu:
          </div>

          <div className="space-y-2 pt-1">
            <div className="p-3 border rounded-xl bg-emerald-50/60 border-emerald-200">
              <div className="font-semibold text-emerald-900 text-xs mb-1">
                Phương án 1: Chỉ công nhận các bạn ĐÃ TRỰC
              </div>
              <div className="text-[11px] text-gray-600 mb-2">
                Hệ thống duyệt <strong>ĐẠT</strong> cho {checkedTasks.length} bạn đã nộp. Những bạn còn lại
                ({uncheckedTasks.length} bạn) sẽ bị ghi nhận <strong>CHƯA ĐẠT</strong> và tiếp tục quay bốc thăm ở buổi sau.
              </div>
              <Button
                type="primary"
                block
                className="bg-emerald-600 hover:bg-emerald-500 font-semibold text-xs h-8"
                loading={updatingTask}
                onClick={() => executeApproveAll(false)}
              >
                Chỉ duyệt cho các bạn đã nộp ({checkedTasks.length} bạn)
              </Button>
            </div>

            <div className="p-3 border rounded-xl bg-gray-50 border-gray-200">
              <div className="font-semibold text-gray-800 text-xs mb-1">
                Phương án 2: Duyệt ĐẠT cho toàn bộ cả nhóm
              </div>
              <div className="text-[11px] text-gray-500 mb-2">
                Áp dụng nếu Admin xác nhận cả nhóm đều có mặt trực đầy đủ nhưng quên chụp ảnh. Cả {totalTasks} bạn
                đều được tính hoàn thành vòng trực này.
              </div>
              <Button
                block
                className="text-xs h-8"
                loading={updatingTask}
                onClick={() => executeApproveAll(true)}
              >
                Duyệt ĐẠT cả {totalTasks} bạn
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Modal từ chối cả ca */}
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
            placeholder="Ví dụ: Bàn học dãy 2 chưa lau sạch, rác cuối phòng chưa đổ..."
          />
        </div>
      </Modal>
    </>
  );
};
