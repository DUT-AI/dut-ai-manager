import React, { useState } from 'react';
import {
  Table,
  Tag,
  Button,
  Card,
  Typography,
  Space,
  Select,
  Tooltip,
  Alert,
  Popconfirm,
  Tabs,
  Badge,
  message,
} from 'antd';
import {
  UploadOutlined,
  EyeOutlined,
  CalendarOutlined,
  HistoryOutlined,
  FilterOutlined,
  ExclamationCircleOutlined,
  CarryOutOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UndoOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import { useAuth } from '@/features/auth';
import { useDutyManagement } from '../hooks/useDutyManagement';
import { WeeklyDutyCalendar } from '../components/WeeklyDutyCalendar';
import { SubmitDutyModal } from '../components/SubmitDutyModal';
import { DutyDetailModal } from '../components/DutyDetailModal';
import { CreateDutyModal, type CreateDutyFormValues } from '../components/CreateDutyModal';
import { dutyService } from '../services/duty.service';
import type { DutyResponse } from '../types/duty.types';

dayjs.extend(isoWeek);

const { Title, Text } = Typography;

export const DutyManagementPage: React.FC = () => {
  const { user, hasPermission } = useAuth();

  const canManage =
    hasPermission('duty:create') ||
    user?.role_names?.some((r) =>
      ['admin', 'hr'].includes(r.toLowerCase())
    ) || false;

  const [currentDate, setCurrentDate] = useState<Dayjs>(dayjs());
  const [activeTab, setActiveTab] = useState<string>('calendar');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [isCreateDutyModalOpen, setIsCreateDutyModalOpen] = useState(false);
  const [editingDuty, setEditingDuty] = useState<DutyResponse | null>(null);

  const {
    weeklySchedule,
    loadingWeekly,
    fetchWeeklySchedule,
    duties,
    totalDuties,
    loadingDuties,
    page,
    setPage,
    pageSize,
    setPageSize,
    fetchDuties,
    toggleSchedule,
    selectedDuty,
    isSubmitModalOpen,
    setIsSubmitModalOpen,
    isDetailModalOpen,
    setIsDetailModalOpen,
    targetDutyIdForSubmit,
    openSubmitModal,
    openDetailModal,
    approveDuty,
    rejectDuty,
    updateDuty,
    deleteDuty,
    restoreDuty,
    batchCreateDuties,
  } = useDutyManagement();

  // Điều hướng tuần
  const goToPrevWeek = () => {
    const prev = currentDate.subtract(1, 'week');
    setCurrentDate(prev);
    fetchWeeklySchedule(prev.format('YYYY-MM-DD'));
  };

  const goToNextWeek = () => {
    const next = currentDate.add(1, 'week');
    setCurrentDate(next);
    fetchWeeklySchedule(next.format('YYYY-MM-DD'));
  };

  const goToToday = () => {
    const now = dayjs();
    setCurrentDate(now);
    fetchWeeklySchedule(now.format('YYYY-MM-DD'));
  };

  const handleCreateOrUpdateDuty = async (values: CreateDutyFormValues) => {
    if (editingDuty) {
      await updateDuty(editingDuty.id, {
        team_id: values.team_id,
        duty_date: values.duty_date,
        start_time: values.start_time,
        end_time: values.end_time,
        checklist: values.checklist,
        note: values.note,
      });
    } else {
      const teamIds =
        values.team_ids && values.team_ids.length > 0
          ? values.team_ids
          : values.team_id
            ? [values.team_id]
            : [];

      await batchCreateDuties({
        team_ids: teamIds,
        duty_date: values.duty_date,
        start_time: values.start_time,
        end_time: values.end_time,
        checklist: values.checklist,
        note: values.note,
      });
    }
    await fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
    await fetchDuties();
    setEditingDuty(null);
  };

  const handleEditDutyById = async (dutyId: number) => {
    const found = duties.find((d) => d.id === dutyId);
    if (found) {
      setEditingDuty(found);
      setIsCreateDutyModalOpen(true);
    } else {
      try {
        const res = await dutyService.getDutyById(dutyId);
        if (res.data) {
          setEditingDuty(res.data);
          setIsCreateDutyModalOpen(true);
        }
      } catch {
        // Fallback
      }
    }
  };

  const handleDeleteDutyById = async (dutyId: number) => {
    await deleteDuty(dutyId);
    fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
  };

  const handleStatusFilterChange = (val: string | undefined) => {
    setStatusFilter(val);
    fetchDuties({ page: 1, status: val });
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

  const columns: ColumnsType<DutyResponse> = [
    {
      title: 'Ngày trực',
      dataIndex: 'duty_date',
      key: 'duty_date',
      width: 125,
      render: (val) => (
        <span className="font-semibold text-gray-800 whitespace-nowrap">
          {dayjs(val).format('DD/MM/YYYY')}
        </span>
      ),
    },
    {
      title: 'Nhóm phụ trách',
      dataIndex: 'team_name',
      key: 'team_name',
      render: (val, record) => {
        if (record.team_names && record.team_names.length > 1) {
          return (
            <div className="flex flex-wrap gap-1 max-w-[280px]">
              {record.team_names.map((name, i) => (
                <Tag key={i} color={i === 0 ? 'blue' : 'cyan'} className="m-0 text-xs">
                  {name}
                </Tag>
              ))}
            </div>
          );
        }
        return (
          <span className="font-medium text-blue-700 whitespace-nowrap">
            {val || `Nhóm ID: ${Array.isArray(record.team_id) ? record.team_id.join(', ') : record.team_id}`}
          </span>
        );
      },
    },
    {
      title: 'Buổi meeting',
      dataIndex: 'meeting_title',
      key: 'meeting_title',
      render: (val) =>
        val ? (
          <span className="text-gray-700 whitespace-nowrap">{val}</span>
        ) : (
          <span className="text-gray-400 font-medium whitespace-nowrap">Ca trực tự do</span>
        ),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      align: 'center',
      render: (val) => <div className="whitespace-nowrap">{renderStatusTag(val)}</div>,
    },
    {
      title: 'Người nộp',
      dataIndex: 'submitted_by_name',
      key: 'submitted_by_name',
      width: 170,
      render: (val, record) =>
        val ? (
          <div className="whitespace-nowrap">
            <div className="font-semibold text-gray-800 truncate max-w-[160px]">{val}</div>
            <div className="text-xs text-gray-400">
              {record.submitted_at
                ? dayjs(record.submitted_at.replace(/Z|[+-]\d{2}:\d{2}$/, '')).format('HH:mm - DD/MM/YYYY')
                : ''}
            </div>
          </div>
        ) : (
          <Text type="secondary" className="whitespace-nowrap">Chưa nộp</Text>
        ),
    },
    {
      title: 'Thành phẩm',
      dataIndex: 'evidence_image_urls',
      key: 'evidence_image_urls',
      width: 110,
      align: 'center',
      render: (urls: string[]) => (
        <div className="whitespace-nowrap">
          {urls && urls.length > 0 ? (
            <Tag color="cyan">{urls.length} ảnh</Tag>
          ) : (
            <Text type="secondary">0 ảnh</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Hành động',
      key: 'action',
      width: 260,
      render: (_, record) => {
        const isCancelled = record.status === 'CANCELLED';
        const isCompleted = record.status === 'COMPLETED';

        return (
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            {/* Nút Hồi phục cho ca bị CANCELLED */}
            {canManage && isCancelled && (
              <Tooltip title="Hồi phục ca trực nhật về lại trạng thái hoạt động">
                <Button
                  type="primary"
                  size="small"
                  icon={<UndoOutlined />}
                  onClick={() => restoreDuty(record.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 border-none flex items-center justify-center text-xs"
                >
                  Hồi phục
                </Button>
              </Tooltip>
            )}

            {/* Chi tiết */}
            <Tooltip title="Xem chi tiết ca trực">
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={() => openDetailModal(record.id)}
                className="flex items-center justify-center text-xs"
              >
                Chi tiết
              </Button>
            </Tooltip>

            {/* Sửa (chỉ cho ca chưa xong và chưa bị hủy) */}
            {canManage && !isCompleted && !isCancelled && (
              <Tooltip title="Chỉnh sửa checklist & ghi chú">
                <Button
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => {
                    setEditingDuty(record);
                    setIsCreateDutyModalOpen(true);
                  }}
                  className="flex items-center justify-center text-xs"
                >
                  Sửa
                </Button>
              </Tooltip>
            )}

            {/* Xóa (chỉ cho ca chưa xong và chưa bị hủy) */}
            {canManage && !isCompleted && !isCancelled && (
              <Popconfirm
                title="Hủy/xóa ca trực nhật"
                description={`Bạn có chắc chắn muốn hủy ca trực ngày ${dayjs(record.duty_date).format('DD/MM/YYYY')} của ${record.team_name || 'nhóm này'}? Ca trực sẽ chuyển sang trạng thái CANCELLED trong lịch sử.`}
                onConfirm={async () => {
                  if (record.status === 'AWAITING_APPROVAL') {
                    message.warning('Ca trực nhật đang chờ Admin/HR duyệt minh chứng, không thể xóa!');
                    return;
                  }
                  await deleteDuty(record.id);
                }}
                okText="Hủy ca"
                cancelText="Quay lại"
                okButtonProps={{ danger: true }}
              >
                <Tooltip title="Hủy ca trực này">
                  <Button
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    className="flex items-center justify-center text-xs"
                  >
                    Xóa
                  </Button>
                </Tooltip>
              </Popconfirm>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="p-4 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <Title level={2} className="!mb-1 flex items-center gap-2.5 text-gray-800">
            <CarryOutOutlined className="text-blue-600" />
            <span>Quản lý Trực nhật</span>
          </Title>
          <Text type="secondary" className="text-xs">
            Theo dõi, phân công lịch trực nhật theo Meeting hoặc tự do và duyệt minh chứng vệ sinh Phòng học
          </Text>
        </div>
      </div>

      {/* Thông báo ca chờ duyệt cho Admin/HR */}
      {canManage && (weeklySchedule?.some((d) => d.status === 'AWAITING_APPROVAL') || duties.some((d) => d.status === 'AWAITING_APPROVAL')) && (
        <Alert
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined className="text-amber-500 text-lg" />}
          message={
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="font-semibold text-amber-900 text-sm">
                  🔔 Có ca trực nhật đang chờ Admin/HR duyệt minh chứng!
                </span>
                <div className="text-xs text-amber-700 mt-0.5">
                  Học viên đã hoàn thành dọn dẹp và gửi ảnh minh chứng. Vui lòng kiểm tra và duyệt đạt chuẩn hoặc từ chối để các bạn làm lại trước 22:00.
                </div>
              </div>
              <Button
                type="primary"
                size="small"
                className="bg-amber-600 hover:bg-amber-500 border-none self-start sm:self-auto shrink-0 font-medium"
                onClick={() => {
                  setActiveTab('calendar');
                }}
              >
                Xem ca chờ duyệt
              </Button>
            </div>
          }
          className="border-amber-200 bg-amber-50/90 rounded-xl shadow-sm py-3 px-4"
        />
      )}

      {/* Tabs phân tách Lịch Trực Tuần & Lịch Sử Danh Sách */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="line"
        size="large"
        items={[
          {
            key: 'calendar',
            label: (
              <span className="flex items-center gap-2 font-medium px-1">
                <CalendarOutlined className="text-blue-600" />
                <span>Lịch Trực Tuần</span>
                {weeklySchedule.some((d) => d.status === 'AWAITING_APPROVAL') && (
                  <Badge
                    count={weeklySchedule.filter((d) => d.status === 'AWAITING_APPROVAL').length}
                    className="ml-1.5"
                    style={{ backgroundColor: '#f59e0b' }}
                  />
                )}
              </span>
            ),
            children: (
              <Card className="rounded-xl border shadow-sm">
                <WeeklyDutyCalendar
                  schedule={weeklySchedule}
                  loading={loadingWeekly}
                  canManage={canManage}
                  currentDate={currentDate}
                  onPrevWeek={goToPrevWeek}
                  onNextWeek={goToNextWeek}
                  onToday={goToToday}
                  onOpenCreateModal={() => setIsCreateDutyModalOpen(true)}
                  onToggleSchedule={async (teamId, dutyDate, enabled, options) => {
                    await toggleSchedule(teamId, dutyDate, enabled, options);
                    fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
                  }}
                  onOpenSubmitModal={openSubmitModal}
                  onOpenDetailModal={openDetailModal}
                  onApproveDuty={approveDuty}
                  onRejectDuty={rejectDuty}
                  onEditDuty={handleEditDutyById}
                  onDeleteDuty={handleDeleteDutyById}
                />
              </Card>
            ),
          },
          {
            key: 'history',
            label: (
              <span className="flex items-center gap-2 font-medium px-1">
                <HistoryOutlined className="text-emerald-600" />
                <span>Lịch Sử Ca Trực</span>
              </span>
            ),
            children: (
              <Card
                className="rounded-xl border shadow-sm"
                title={
                  <div className="flex items-center gap-2">
                    <HistoryOutlined className="text-blue-600" />
                    <span>Lịch Sử Ca Trực Nhật</span>
                  </div>
                }
                extra={
                  <Space>
                    <FilterOutlined className="text-gray-400" />
                    <Select
                      placeholder="Lọc trạng thái lịch sử"
                      allowClear
                      className="w-56"
                      value={statusFilter}
                      onChange={handleStatusFilterChange}
                      options={[
                        { label: 'Tất cả lịch sử', value: '' },
                        { label: 'COMPLETED', value: 'COMPLETED' },
                        { label: 'VIOLATED', value: 'VIOLATED' },
                        { label: 'CANCELLED', value: 'CANCELLED' },
                      ]}
                    />
                  </Space>
                }
              >
                <Table
                  columns={columns}
                  dataSource={duties}
                  rowKey="id"
                  loading={loadingDuties}
                  scroll={{ x: 'max-content' }}
                  pagination={{
                    current: page,
                    pageSize: pageSize,
                    total: totalDuties,
                    onChange: (p, ps) => {
                      setPage(p);
                      setPageSize(ps);
                      fetchDuties({ page: p, page_size: ps, status: statusFilter });
                    },
                    showSizeChanger: true,
                    pageSizeOptions: ['5', '10', '20', '50'],
                  }}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* Modal nộp minh chứng */}
      <SubmitDutyModal
        isOpen={isSubmitModalOpen}
        dutyId={targetDutyIdForSubmit}
        onClose={() => setIsSubmitModalOpen(false)}
        onSuccess={() => {
          fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
          fetchDuties();
        }}
      />

      {/* Modal chi tiết ca trực */}
      <DutyDetailModal
        open={isDetailModalOpen}
        duty={selectedDuty}
        canManage={canManage}
        onClose={() => setIsDetailModalOpen(false)}
        onApprove={async (id) => {
          await approveDuty(id);
          fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
          fetchDuties();
        }}
        onReject={async (id, reason) => {
          await rejectDuty(id, reason);
          fetchWeeklySchedule(currentDate.format('YYYY-MM-DD'));
          fetchDuties();
        }}
      />

      {/* Modal tạo hoặc chỉnh sửa lịch trực nhật */}
      <CreateDutyModal
        isOpen={isCreateDutyModalOpen}
        initialDuty={editingDuty}
        existingSchedule={weeklySchedule}
        onClose={() => {
          setIsCreateDutyModalOpen(false);
          setEditingDuty(null);
        }}
        onSubmit={handleCreateOrUpdateDuty}
      />
    </div>
  );
};
