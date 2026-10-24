import React, { useState, useMemo } from 'react';
import {
  Card,
  Switch,
  Tag,
  Button,
  Typography,
  Space,
  Input,
  Modal,
  Tooltip,
  Popconfirm,
  Select,
} from 'antd';
import {
  CarryOutOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  UploadOutlined,
  LeftOutlined,
  RightOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type { WeeklyDutyClassDto } from '../types/duty.types';

const { Title, Text } = Typography;

interface WeeklyDutyCalendarProps {
  schedule: WeeklyDutyClassDto[];
  loading: boolean;
  canManage: boolean;
  currentDate?: Dayjs;
  onPrevWeek?: () => void;
  onNextWeek?: () => void;
  onToday?: () => void;
  onOpenCreateModal?: () => void;
  onOpenSubmitModal?: (dutyId: number) => void;
  onToggleSchedule: (
    teamId: number | number[],
    dutyDate: string,
    enabled: boolean,
    options?: {
      meeting_id?: number | null;
      start_time?: string | null;
      end_time?: string | null;
    }
  ) => void;
  onOpenDetailModal: (dutyId: number) => void;
  onApproveDuty?: (dutyId: number) => void;
  onRejectDuty?: (dutyId: number, reason: string) => void;
  onEditDuty?: (dutyId: number) => void;
  onDeleteDuty?: (dutyId: number) => void;
}

export const WeeklyDutyCalendar: React.FC<WeeklyDutyCalendarProps> = ({
  schedule,
  loading,
  canManage,
  currentDate,
  onPrevWeek,
  onNextWeek,
  onToday,
  onOpenCreateModal,
  onToggleSchedule,
  onOpenSubmitModal,
  onOpenDetailModal,
  onApproveDuty,
  onRejectDuty,
  onEditDuty,
  onDeleteDuty,
}) => {
  const [rejectingDutyId, setRejectingDutyId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [scheduleFilter, setScheduleFilter] = useState<'ALL' | 'SCHEDULED' | 'NOT_SCHEDULED'>('ALL');

  // Lọc danh sách tuần: Luôn ẩn các ca đã COMPLETED khỏi Tab 1 (theo yêu cầu)
  const displaySchedule = useMemo(() => {
    const activeSchedule = schedule.filter((item) => item.status !== 'COMPLETED');
    if (scheduleFilter === 'SCHEDULED') {
      return activeSchedule.filter((item) => item.is_scheduled);
    }
    if (scheduleFilter === 'NOT_SCHEDULED') {
      return activeSchedule.filter((item) => !item.is_scheduled);
    }
    return activeSchedule;
  }, [schedule, scheduleFilter]);

  const handleConfirmReject = () => {
    if (rejectingDutyId && onRejectDuty) {
      onRejectDuty(
        rejectingDutyId,
        rejectionReason || 'Vệ sinh chưa đạt yêu cầu, vui lòng dọn dẹp và nộp lại'
      );
      setRejectingDutyId(null);
      setRejectionReason('');
    }
  };

  const renderDutyStatusTag = (status: string | null) => {
    switch (status) {
      case 'COMPLETED':
        return <Tag color="success">COMPLETED</Tag>;
      case 'AWAITING_APPROVAL':
        return (
          <Tag color="gold" className="font-semibold">
            AWAITING APPROVAL
          </Tag>
        );
      case 'REJECTED':
        return (
          <Tag color="error" className="font-semibold">
            REJECTED
          </Tag>
        );
      case 'VIOLATED':
        return <Tag color="error">VIOLATED</Tag>;
      case 'CANCELLED':
        return <Tag color="default">CANCELLED</Tag>;
      case 'PENDING':
        return <Tag color="processing">PENDING</Tag>;
      case 'NO_MEETING':
        return <Tag color="default">NO MEETING</Tag>;
      case 'NOT_SCHEDULED':
      default:
        return <Tag color="default">NOT SCHEDULED</Tag>;
    }
  };

  return (
    <div>
      {/* Header với điều hướng tuần, bộ lọc & nút tạo lịch tự do */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3 mb-5 pb-3 border-b border-gray-100">
        <div>
          <Title level={4} className="!mb-1 flex items-center gap-2 text-gray-800">
            <CarryOutOutlined className="text-blue-600" />
            <span>Lịch Trực Nhật Tuần</span>
            {currentDate && (
              <span className="text-xs font-normal text-gray-500">
                (Tuần {currentDate.isoWeek()} • {currentDate.startOf('isoWeek').format('DD/MM')} – {currentDate.endOf('isoWeek').format('DD/MM/YYYY')})
              </span>
            )}
          </Title>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Bộ lọc lên lịch hay chưa theo yêu cầu */}
          <Select
            size="small"
            value={scheduleFilter}
            onChange={setScheduleFilter}
            className="w-44"
            options={[
              { label: 'Tất cả ca trực', value: 'ALL' },
              { label: 'Đã lên lịch (ON)', value: 'SCHEDULED' },
              { label: 'Chưa lên lịch (OFF)', value: 'NOT_SCHEDULED' },
            ]}
          />

          {onPrevWeek && onToday && onNextWeek && (
            <Button.Group size="small">
              <Button icon={<LeftOutlined />} onClick={onPrevWeek} />
              <Button onClick={onToday}>Hôm nay</Button>
              <Button icon={<RightOutlined />} onClick={onNextWeek} />
            </Button.Group>
          )}

          {canManage && onOpenCreateModal && (
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={onOpenCreateModal}
              className="bg-blue-600 hover:bg-blue-500"
            >
              Tạo ca tự do
            </Button>
          )}
        </div>
      </div>

      {/* Grid danh sách ca trực theo Meeting / Tuần */}
      {displaySchedule.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <CarryOutOutlined className="text-3xl mb-2 text-gray-300" />
          <div className="text-sm font-medium">
            {schedule.length === 0
              ? 'Chưa có lịch Meeting hoặc ca trực nào trong tuần này'
              : 'Không có ca trực nào phù hợp với bộ lọc'}
          </div>
          {schedule.length > 0 && scheduleFilter !== 'ALL' && (
            <Button
              type="link"
              size="small"
              onClick={() => setScheduleFilter('ALL')}
              className="mt-1"
            >
              Xem tất cả ca trực
            </Button>
          )}
          {canManage && onOpenCreateModal && schedule.length === 0 && (
            <Button
              type="dashed"
              size="small"
              icon={<PlusOutlined />}
              onClick={onOpenCreateModal}
              className="mt-3"
            >
              Tạo lịch trực tự do ngay
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {displaySchedule.map((item, idx) => {
            const hasMeeting = item.has_meeting;
            const isScheduled = item.is_scheduled;
            const isCompleted = item.status === 'COMPLETED';
            const isAwaitingApproval = item.status === 'AWAITING_APPROVAL';
            const isRejected = item.status === 'REJECTED';

            return (
              <Card
                key={`${item.duty_date}-${item.team_id}-${item.meeting_id ?? idx}`}
                loading={loading}
                className={`rounded-xl border shadow-sm transition-all hover:shadow-md ${isCompleted
                  ? 'border-green-300 bg-green-50/20'
                  : isAwaitingApproval
                    ? 'border-amber-300 bg-amber-50/30'
                    : isRejected
                      ? 'border-rose-300 bg-rose-50/30'
                      : isScheduled
                        ? 'border-blue-300 bg-blue-50/20'
                        : 'border-gray-200 bg-gray-50/40'
                  }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-1.5">
                    <Tag
                      color={hasMeeting ? 'geekblue' : 'default'}
                      className="text-sm font-semibold px-2 py-0.5 !mr-0"
                    >
                      {item.day_name}
                    </Tag>

                    {item.is_time_conflict && (
                      <Tooltip
                        title={
                          item.conflict_message ||
                          'Trùng khung giờ với ca trực khác của nhóm trong ngày'
                        }
                      >
                        <Tag
                          color="warning"
                          className="text-xs font-semibold px-1.5 py-0.5 border-amber-300 bg-amber-50 text-amber-700 cursor-pointer"
                        >
                          ⚠️ Trùng giờ
                        </Tag>
                      </Tooltip>
                    )}

                    {/* Nút sửa/xóa trên tag (chỉ hiển thị khi ca chưa COMPLETED và chưa AWAITING_APPROVAL) */}
                    {canManage && item.duty_id && !isCompleted && !isAwaitingApproval && (
                      <Space size={2} className="ml-1">
                        <Tooltip title="Chỉnh sửa ca trực này">
                          <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined className="text-blue-600 text-xs" />}
                            className="h-6 w-6 p-0 hover:bg-blue-50 flex items-center justify-center rounded"
                            onClick={() => onEditDuty && onEditDuty(item.duty_id!)}
                          />
                        </Tooltip>
                        <Popconfirm
                          title="Xóa ca trực này?"
                          description={`Bạn có chắc muốn xóa ca trực ngày ${dayjs(item.duty_date).format('DD/MM/YYYY')} của ${item.team_name}?`}
                          onConfirm={() => onDeleteDuty && onDeleteDuty(item.duty_id!)}
                          okText="Xóa"
                          cancelText="Hủy"
                          okButtonProps={{ danger: true }}
                        >
                          <Tooltip title="Xóa ca trực này">
                            <Button
                              type="text"
                              size="small"
                              danger
                              icon={<DeleteOutlined className="text-rose-500 text-xs" />}
                              className="h-6 w-6 p-0 hover:bg-rose-50 flex items-center justify-center rounded"
                            />
                          </Tooltip>
                        </Popconfirm>
                      </Space>
                    )}
                  </div>

                  <Text strong className="text-gray-500 text-xs">
                    {dayjs(item.duty_date).format('DD/MM/YYYY')}
                  </Text>
                </div>

                <div className="my-2 min-h-[32px] flex items-center">
                  {item.team_names && item.team_names.length > 1 ? (
                    <div className="flex flex-wrap gap-1.5 w-full">
                      {item.team_names.map((tName, idx) => (
                        <Tag
                          key={idx}
                          color={idx === 0 ? "blue" : "cyan"}
                          className="font-medium text-xs px-2 py-0.5 rounded m-0 max-w-full truncate"
                        >
                          👥 {tName}
                        </Tag>
                      ))}
                    </div>
                  ) : (
                    <Text strong className="block text-base text-gray-800 line-clamp-1">
                      {item.team_name}
                    </Text>
                  )}
                </div>

                {/* Thông tin buổi Meeting (Học) hoặc Khung giờ Ca tự do */}
                {hasMeeting ? (
                  <div className="text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 p-2 rounded-lg mb-3">
                    <div className="flex items-center gap-1 font-semibold">
                      <ClockCircleOutlined />
                      <span>Meeting: {item.meeting_time}</span>
                    </div>
                    <div className="truncate text-gray-600 mt-0.5">
                      {item.meeting_title || 'Đã lên lịch Meeting'}
                    </div>
                  </div>
                ) : item.meeting_time ? (
                  <div className="text-xs text-sky-800 bg-sky-50 border border-sky-100 p-2 rounded-lg mb-3">
                    <div className="flex items-center justify-between font-semibold">
                      <div className="flex items-center gap-1">
                        <ClockCircleOutlined className="text-sky-600" />
                        <span>Trực nhật: {item.meeting_time}</span>
                      </div>
                      <Tag color="cyan" className="!mr-0 text-[10px] px-1.5 py-0 leading-tight">
                        Tự do
                      </Tag>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-600 bg-slate-50 border border-slate-200/80 px-2.5 py-1.5 rounded-lg mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                      <span className="font-medium">Ca trực tự do</span>
                    </div>
                    <Tag color="default" className="!mr-0 text-[10px] px-1.5 py-0 leading-tight">
                      Chưa set giờ
                    </Tag>
                  </div>
                )}

                <div className="py-2 border-t border-b border-gray-100 my-2 flex justify-between items-center">
                  <Text className="text-xs text-gray-500">Lên lịch trực nhật:</Text>
                  {canManage ? (
                    <Tooltip
                      title={
                        isCompleted
                          ? 'Ca trực nhật đã hoàn thành nghiệm thu (COMPLETED), không thể tắt!'
                          : isAwaitingApproval
                            ? 'Ca trực nhật đang chờ duyệt minh chứng, không thể tắt!'
                            : undefined
                      }
                    >
                      <Switch
                        disabled={isCompleted || isAwaitingApproval}
                        checked={isScheduled}
                        onChange={(checked) => {
                          onToggleSchedule(item.team_id, item.duty_date, checked, {
                            meeting_id: item.meeting_id,
                            start_time: item.start_time ? String(item.start_time) : null,
                            end_time: item.end_time ? String(item.end_time) : null,
                          });
                        }}
                        checkedChildren="ON"
                        unCheckedChildren="OFF"
                      />
                    </Tooltip>
                  ) : (
                    <Text strong>{isScheduled ? 'ON' : 'OFF'}</Text>
                  )}
                </div>

                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500">Trạng thái:</span>
                    {renderDutyStatusTag(item.status)}
                  </div>

                  {item.submitted_by_name && (
                    <div className="text-xs text-green-700 bg-green-100/60 p-1.5 rounded mt-2">
                      <CheckCircleOutlined className="mr-1" />
                      Đại diện nộp: <strong>{item.submitted_by_name}</strong>
                    </div>
                  )}

                  {/* Hiển thị ghi chú / mô tả phân công nếu có */}
                  {item.note && (
                    <div className="text-xs text-indigo-950 bg-indigo-50/80 border border-indigo-100 p-2 rounded mt-2">
                      <span className="font-semibold block text-[11px] text-indigo-700">📝 Ghi chú phân công:</span>
                      <span className="line-clamp-2 text-gray-700">{item.note}</span>
                    </div>
                  )}

                  {/* Hiển thị lý do nếu bị từ chối */}
                  {isRejected && item.rejection_reason && (
                    <div className="text-xs text-rose-700 bg-rose-100/70 border border-rose-200 p-2 rounded mt-2">
                      <span className="font-semibold block">⚠️ Lý do từ chối:</span>
                      <span>{item.rejection_reason}</span>
                      <span className="block mt-1 text-[11px] text-rose-600 italic">
                        Vui lòng vệ sinh lại và nộp minh chứng trước 22h00 để không tính vi phạm!
                      </span>
                    </div>
                  )}
                </div>

                {/* Khu vực duyệt nhanh cho Admin / HR khi có người nộp bài */}
                {canManage && isAwaitingApproval && item.duty_id && (
                  <div className="bg-amber-50 border border-amber-200 p-2.5 rounded-lg mb-3">
                    <div className="text-xs text-amber-800 font-semibold mb-2 flex items-center gap-1">
                      <span>🔔 Minh chứng đang chờ duyệt:</span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="primary"
                        size="small"
                        icon={<CheckCircleOutlined />}
                        className="bg-emerald-600 hover:bg-emerald-500 border-none flex-1 font-medium"
                        onClick={() => onApproveDuty && onApproveDuty(item.duty_id!)}
                      >
                        Duyệt đạt
                      </Button>
                      <Button
                        danger
                        size="small"
                        icon={<CloseCircleOutlined />}
                        className="flex-1 font-medium"
                        onClick={() => setRejectingDutyId(item.duty_id)}
                      >
                        Từ chối
                      </Button>
                    </div>
                  </div>
                )}

                {/* Nút hành động */}
                <div className="flex gap-2 pt-1 border-t border-gray-100">
                  {/* Nếu bị từ chối: Quản lý hoặc thành viên trong nhóm trực thao tác nộp lại */}
                  {isRejected && item.duty_id && (
                    <Button
                      type="primary"
                      danger
                      size="small"
                      icon={<UploadOutlined />}
                      className="flex-1 font-medium text-xs"
                      onClick={() => onOpenSubmitModal(item.duty_id!)}
                    >
                      Nộp lại
                    </Button>
                  )}

                  {isScheduled && !isCompleted && !isAwaitingApproval && !isRejected && item.duty_id && (
                    <Button
                      type="primary"
                      size="small"
                      icon={<UploadOutlined />}
                      className="flex-1 font-medium"
                      onClick={() => onOpenSubmitModal(item.duty_id!)}
                    >
                      Nộp minh chứng
                    </Button>
                  )}

                  {item.duty_id && (
                    <Button
                      size="small"
                      icon={<EyeOutlined />}
                      className="flex-1 text-gray-600"
                      onClick={() => onOpenDetailModal(item.duty_id!)}
                    >
                      Chi tiết
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal nhập lý do từ chối */}
      <Modal
        title="Từ chối minh chứng trực nhật"
        open={rejectingDutyId !== null}
        onCancel={() => {
          setRejectingDutyId(null);
          setRejectionReason('');
        }}
        onOk={handleConfirmReject}
        okText="Xác nhận từ chối"
        okButtonProps={{ danger: true }}
        cancelText="Hủy"
        destroyOnClose
      >
        <div className="py-2">
          <Text className="text-gray-600 block mb-2">
            Vui lòng nhập lý do từ chối để học viên biết và dọn dẹp lại trước hạn chót (22h00):
          </Text>
          <Input.TextArea
            rows={3}
            placeholder="Ví dụ: Bàn học số 3 chưa lau, sàn nhà còn rác ở góc cuối phòng..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
};
