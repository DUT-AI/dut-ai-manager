import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  Form,
  Select,
  DatePicker,
  TimePicker,
  Checkbox,
  Input,
  Button,
  Divider,
  Space,
  Tooltip,
  Alert,
} from 'antd';
import {
  CarryOutOutlined,
  EditOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  ClockCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { teamService } from '@/features/teams/services/team.service';
import type { DutyResponse, DutyChecklistItem, WeeklyDutyClassDto } from '../types/duty.types';

export interface CreateDutyFormValues {
  team_id?: number;
  team_ids?: number[];
  duty_date: string;
  start_time?: string | null;
  end_time?: string | null;
  checklist: DutyChecklistItem[];
  note?: string;
}

interface CreateDutyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (values: CreateDutyFormValues) => Promise<void>;
  initialDuty?: DutyResponse | null;
  existingSchedule?: WeeklyDutyClassDto[];
}

const DEFAULT_CHECKLIST: DutyChecklistItem[] = [
  { id: '1', title: '🧹 Quét & lau sàn nhà', checked: true },
  { id: '2', title: '🪑 Lau bàn ghế học tập', checked: true },
  { id: '3', title: '💨 Lau quạt trần / quạt điện', checked: false },
  { id: '4', title: '🗄️ Lau tủ tài liệu & thiết bị', checked: false },
  { id: '5', title: '🪟 Lau cửa kính & cửa sổ phòng Lab', checked: false },
];

export const CreateDutyModal: React.FC<CreateDutyModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialDuty,
  existingSchedule = [],
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [teams, setTeams] = useState<Array<{ id: number; name: string }>>([]);

  // Quản lý CRUD checklist động
  const [checklist, setChecklist] = useState<DutyChecklistItem[]>(DEFAULT_CHECKLIST);
  const [newTitle, setNewTitle] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const isEditMode = Boolean(initialDuty);

  // Theo dõi các field để phát hiện trùng giờ realtime
  const watchedDate = Form.useWatch('duty_date', form) as Dayjs | undefined;
  const watchedTimeRange = Form.useWatch('time_range', form) as [Dayjs, Dayjs] | undefined;
  const watchedTeamId = Form.useWatch('team_id', form) as number | undefined;
  const watchedTeamIds = Form.useWatch('team_ids', form) as number[] | undefined;

  useEffect(() => {
    if (isOpen) {
      const loadTeams = async () => {
        try {
          const res = await teamService.getTeamOptions();
          if (res.data) {
            setTeams(res.data);
          } else {
            const listRes = await teamService.getTeams(0, 100);
            if (listRes.data) {
              setTeams(
                listRes.data.map((t) => ({
                  id: t.id,
                  name: t.team_name,
                }))
              );
            }
          }
        } catch {
          try {
            const listRes = await teamService.getTeams(0, 100);
            if (listRes.data) {
              setTeams(
                listRes.data.map((t) => ({
                  id: t.id,
                  name: t.team_name,
                }))
              );
            }
          } catch {
            console.error('Failed to load teams');
          }
        }
      };
      loadTeams();

      if (initialDuty) {
        let initialTimeRange: [Dayjs, Dayjs] | undefined = undefined;
        if (initialDuty.start_time && initialDuty.end_time) {
          initialTimeRange = [
            dayjs(initialDuty.start_time, 'HH:mm:ss'),
            dayjs(initialDuty.end_time, 'HH:mm:ss'),
          ];
        }

        form.setFieldsValue({
          team_id: Array.isArray(initialDuty.team_id) ? initialDuty.team_id[0] : initialDuty.team_id,
          team_ids: Array.isArray(initialDuty.team_id) ? initialDuty.team_id : (initialDuty.team_id ? [initialDuty.team_id] : []),
          duty_date: dayjs(initialDuty.duty_date),
          time_range: initialTimeRange,
          note: initialDuty.note || '',
        });

        if (initialDuty.checklist && initialDuty.checklist.length > 0) {
          setChecklist(initialDuty.checklist);
        } else {
          setChecklist(DEFAULT_CHECKLIST);
        }
      } else {
        form.setFieldsValue({
          duty_date: dayjs(),
          time_range: undefined,
          team_ids: [],
          note: '',
        });
        setChecklist(DEFAULT_CHECKLIST);
      }
      setEditingId(null);
      setNewTitle('');
    }
  }, [isOpen, initialDuty, form]);

  // Kiểm tra xung đột trùng giờ
  const conflictWarnings = useMemo(() => {
    if (!watchedDate || !watchedTimeRange || !watchedTimeRange[0] || !watchedTimeRange[1]) {
      return [];
    }
    const selectedTeamIds: number[] = isEditMode
      ? (watchedTeamId ? [watchedTeamId] : [])
      : (watchedTeamIds || []);

    if (selectedTeamIds.length === 0) return [];

    const dateStr = watchedDate.format('YYYY-MM-DD');
    const startMins = watchedTimeRange[0].hour() * 60 + watchedTimeRange[0].minute();
    const endMins = watchedTimeRange[1].hour() * 60 + watchedTimeRange[1].minute();

    const conflicts: string[] = [];

    for (const tId of selectedTeamIds) {
      const teamObj = teams.find((t) => t.id === tId);
      const teamName = teamObj ? teamObj.name : `Nhóm #${tId}`;

      // Tìm trong existingSchedule xem nhóm này ngày đó có ca nào bị overlap không
      const matched = existingSchedule.filter((item) => {
        const itemTeamIds = Array.isArray(item.team_id) ? item.team_id : [item.team_id];
        if (!item.is_scheduled || !itemTeamIds.includes(tId) || item.duty_date !== dateStr) {
          return false;
        }
        // Nếu đang edit thì bỏ qua chính ca đang edit
        if (isEditMode && initialDuty && item.duty_id === initialDuty.id) {
          return false;
        }
        if (!item.start_time) return false;

        const [sH, sM] = item.start_time.split(':').map(Number);
        const itemStartMins = sH * 60 + sM;
        let itemEndMins = itemStartMins + 60; // Mặc định nếu ko có end_time
        if (item.end_time) {
          const [eH, eM] = item.end_time.split(':').map(Number);
          itemEndMins = eH * 60 + eM;
        }

        return startMins < itemEndMins && itemStartMins < endMins;
      });

      if (matched.length > 0) {
        const timeStrs = matched
          .map((m) => m.meeting_time || `${m.start_time || ''} - ${m.end_time || ''}`)
          .join(', ');
        conflicts.push(`Nhóm "${teamName}" đã có ca trực trùng giờ (${timeStrs}) trong ngày này`);
      }
    }

    return conflicts;
  }, [watchedDate, watchedTimeRange, watchedTeamId, watchedTeamIds, isEditMode, initialDuty, teams, existingSchedule]);

  // Thêm đầu việc mới
  const handleAddChecklist = () => {
    const trimmed = newTitle.trim();
    if (!trimmed) return;
    const item: DutyChecklistItem = {
      id: `task_${Date.now()}`,
      title: trimmed,
      checked: true,
    };
    setChecklist([...checklist, item]);
    setNewTitle('');
  };

  // Bắt đầu sửa đầu việc
  const handleStartEdit = (item: DutyChecklistItem) => {
    setEditingId(item.id);
    setEditingTitle(item.title);
  };

  // Lưu sửa đầu việc
  const handleSaveEdit = (id: string) => {
    const trimmed = editingTitle.trim();
    if (!trimmed) {
      setEditingId(null);
      return;
    }
    setChecklist(
      checklist.map((it) => (it.id === id ? { ...it, title: trimmed } : it))
    );
    setEditingId(null);
  };

  // Xóa đầu việc
  const handleDeleteChecklist = (id: string) => {
    setChecklist(checklist.filter((it) => it.id !== id));
  };

  // Toggle tick chọn đầu việc
  const handleToggleChecklist = (id: string, checked: boolean) => {
    setChecklist(
      checklist.map((it) => (it.id === id ? { ...it, checked } : it))
    );
  };

  const handleFinish = async (values: {
    team_id?: number;
    team_ids?: number[];
    duty_date: Dayjs;
    time_range?: [Dayjs, Dayjs];
    note?: string;
  }) => {
    try {
      setLoading(true);

      const timeRange = values.time_range;
      const startTime =
        timeRange && timeRange[0] ? timeRange[0].format('HH:mm:ss') : undefined;
      const endTime =
        timeRange && timeRange[1] ? timeRange[1].format('HH:mm:ss') : undefined;

      const payload: CreateDutyFormValues = {
        team_id: isEditMode ? values.team_id : undefined,
        team_ids: isEditMode
          ? undefined
          : (Array.isArray(values.team_ids) ? values.team_ids : [values.team_ids!]),
        duty_date: values.duty_date.format('YYYY-MM-DD'),
        start_time: startTime,
        end_time: endTime,
        checklist: checklist,
        note: values.note?.trim() || undefined,
      };

      await onSubmit(payload);
      form.resetFields();
      onClose();
    } catch {
      // Error handled by parent
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2 text-base font-semibold text-gray-800">
          {isEditMode ? (
            <>
              <EditOutlined className="text-blue-600" />
              <span>Chỉnh Sửa Ca Trực Nhật</span>
            </>
          ) : (
            <>
              <CarryOutOutlined className="text-blue-600" />
              <span>Tạo Lịch Trực Nhật Tự Do</span>
            </>
          )}
        </div>
      }
      open={isOpen}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      okText={isEditMode ? 'Lưu thay đổi' : 'Tạo ca trực'}
      cancelText="Hủy"
      destroyOnClose
      width={640}
    >
      <div className="text-xs text-gray-500 mb-4">
        {isEditMode
          ? 'Admin/HR có thể điều chỉnh ngày, khung giờ trực, nhóm phụ trách và quản lý đầu việc.'
          : 'Admin/HR có thể chọn một hoặc nhiều nhóm phụ trách, cài đặt ngày + khung giờ trực và nội dung công việc.'}
      </div>

      <Form form={form} layout="vertical" onFinish={handleFinish}>
        {/* Hàng 1: Nhóm phụ trách & Ngày trực */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {isEditMode ? (
            <Form.Item
              label="Nhóm phụ trách"
              name="team_id"
              rules={[{ required: true, message: 'Vui lòng chọn nhóm phụ trách' }]}
            >
              <Select
                placeholder="Chọn nhóm"
                showSearch
                optionFilterProp="label"
                options={teams.map((t) => ({
                  label: t.name,
                  value: t.id,
                }))}
              />
            </Form.Item>
          ) : (
            <Form.Item
              label={
                <div className="flex items-center justify-between w-full">
                  <span>Nhóm phụ trách (chọn nhiều nhóm)</span>
                  {teams.length > 0 && (
                    <Button
                      type="link"
                      size="small"
                      className="p-0 h-auto text-xs"
                      onClick={() => {
                        const current = form.getFieldValue('team_ids') || [];
                        if (current.length === teams.length) {
                          form.setFieldsValue({ team_ids: [] });
                        } else {
                          form.setFieldsValue({ team_ids: teams.map((t) => t.id) });
                        }
                      }}
                    >
                      {(form.getFieldValue('team_ids') || []).length === teams.length
                        ? 'Bỏ chọn tất cả'
                        : 'Chọn tất cả'}
                    </Button>
                  )}
                </div>
              }
              name="team_ids"
              rules={[{ required: true, message: 'Vui lòng chọn ít nhất một nhóm phụ trách' }]}
            >
              <Select
                mode="multiple"
                placeholder="Chọn một hoặc nhiều nhóm"
                showSearch
                maxTagCount="responsive"
                optionFilterProp="label"
                options={teams.map((t) => ({
                  label: t.name,
                  value: t.id,
                }))}
              />
            </Form.Item>
          )}

          <Form.Item
            label="Ngày trực"
            name="duty_date"
            rules={[{ required: true, message: 'Vui lòng chọn ngày trực' }]}
          >
            <DatePicker className="w-full" format="DD/MM/YYYY" placeholder="Chọn ngày (dd/mm/yyyy)" />
          </Form.Item>
        </div>

        {/* Hàng 2: Khung giờ trực (Giờ bắt đầu - Giờ kết thúc) */}
        <div className="grid grid-cols-1 gap-4 mb-1">
          <Form.Item
            label={
              <div className="flex items-center gap-1.5">
                <ClockCircleOutlined className="text-blue-600" />
                <span>Khung giờ trực (Bắt đầu – Kết thúc)</span>
              </div>
            }
            name="time_range"
            rules={[{ required: true, message: 'Vui lòng chọn khung giờ trực nhật' }]}
          >
            <TimePicker.RangePicker
              format="HH:mm"
              minuteStep={5}
              placeholder={['Giờ bắt đầu', 'Giờ kết thúc']}
              className="w-full"
            />
          </Form.Item>
        </div>

        {/* Cảnh báo xung đột trùng giờ trực nếu có */}
        {conflictWarnings.length > 0 && (
          <Alert
            type="warning"
            showIcon
            icon={<WarningOutlined className="text-amber-500" />}
            className="mb-4 text-xs bg-amber-50 border-amber-200"
            message={
              <div className="font-semibold text-amber-800">
                Phát hiện trùng khung giờ trực:
              </div>
            }
            description={
              <div className="space-y-1 mt-1 text-amber-700">
                {conflictWarnings.map((msg, i) => (
                  <div key={i}>• {msg}</div>
                ))}
                <div className="italic text-[11px] text-amber-600 mt-1">
                  💡 Bạn vẫn có thể tiếp tục tạo nếu muốn. Hệ thống sẽ gắn nhãn cảnh báo trên Lịch Tuần.
                </div>
              </div>
            }
          />
        )}

        <Divider className="my-2" />

        {/* Khu vực CRUD các Checklist đầu việc */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 font-medium text-gray-800 text-sm">
              <CheckSquareOutlined className="text-indigo-600" />
              <span>Nội dung công việc trực nhật cần thực hiện:</span>
            </div>
            <span className="text-xs text-gray-500">
              ({checklist.filter((c) => c.checked).length}/{checklist.length} việc được chọn)
            </span>
          </div>

          <div className="p-3 bg-gray-50/80 rounded-xl border border-gray-200 space-y-2">
            {/* Danh sách các đầu việc (hỗ trợ Tick, Sửa, Xóa) */}
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-white border border-gray-100 hover:border-indigo-200 transition-all shadow-xs"
                >
                  {editingId === item.id ? (
                    <div className="flex items-center gap-1.5 flex-1 mr-2">
                      <Input
                        size="small"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onPressEnter={() => handleSaveEdit(item.id)}
                        autoFocus
                      />
                      <Button
                        type="primary"
                        size="small"
                        icon={<CheckOutlined />}
                        className="bg-emerald-600 hover:bg-emerald-500"
                        onClick={() => handleSaveEdit(item.id)}
                      />
                      <Button
                        size="small"
                        icon={<CloseOutlined />}
                        onClick={() => setEditingId(null)}
                      />
                    </div>
                  ) : (
                    <Checkbox
                      checked={item.checked}
                      onChange={(e) => handleToggleChecklist(item.id, e.target.checked)}
                      className="flex-1 text-gray-700 text-xs font-medium"
                    >
                      <span className={item.checked ? 'text-gray-900' : 'text-gray-400 line-through'}>
                        {item.title}
                      </span>
                    </Checkbox>
                  )}

                  {editingId !== item.id && (
                    <Space size="small">
                      <Tooltip title="Sửa tên đầu việc">
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined className="text-blue-600 text-xs" />}
                          onClick={() => handleStartEdit(item)}
                          className="hover:bg-blue-50"
                        />
                      </Tooltip>
                      <Tooltip title="Xóa đầu việc này">
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined className="text-xs" />}
                          onClick={() => handleDeleteChecklist(item.id)}
                          className="hover:bg-rose-50"
                        />
                      </Tooltip>
                    </Space>
                  )}
                </div>
              ))}

              {checklist.length === 0 && (
                <div className="text-center py-4 text-xs text-gray-400">
                  Chưa có đầu việc nào. Vui lòng thêm đầu việc bên dưới.
                </div>
              )}
            </div>

            {/* Ô Thêm đầu việc mới (Create) */}
            <div className="pt-2 border-t border-gray-200 flex gap-2">
              <Input
                size="small"
                placeholder="Nhập tên đầu việc mới (ví dụ: Đổ rác, Tắt điều hòa & điện...)"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onPressEnter={handleAddChecklist}
              />
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={handleAddChecklist}
                className="bg-indigo-600 hover:bg-indigo-500 text-xs whitespace-nowrap"
              >
                Thêm việc
              </Button>
            </div>
          </div>
        </div>

        {/* Khung Mô tả / Ghi chú phân công */}
        <div className="mt-4">
          <div className="flex items-center gap-1.5 font-medium text-gray-800 text-sm mb-1.5">
            <FileTextOutlined className="text-indigo-600" />
            <span>Mô tả & Ghi chú phân công</span>
          </div>
          <Form.Item name="note" className="!mb-0">
            <Input.TextArea
              rows={3}
              placeholder="Nhập mô tả cụ thể về khu vực cần dọn, phân công đầu việc hoặc nhắc nhở đặc biệt từ Admin/HR..."
              maxLength={500}
              showCount
            />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  );
};
