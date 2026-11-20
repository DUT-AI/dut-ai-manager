import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  Button,
  Select,
  Input,
  Tag,
  Typography,
  Card,
  Tooltip,
  message,
  Spin,
} from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { dutyService } from '../services/duty.service';
import type {
  DutyChecklistItem,
  TeamCandidateMember,
  DutyCandidatesResponse,
} from '../types/duty.types';

const { Title, Text } = Typography;

interface TaskAssignmentItem {
  id: string;
  title: string;
  assignee_id?: number | null;
  assignee_name?: string | null;
}

interface RandomDutyAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamId: number | number[];
  teamName: string;
  dutyDate: string;
  meetingId?: number | null;
  startTime?: string | null;
  endTime?: string | null;
  onConfirm: (payload: {
    team_id: number | number[];
    duty_date: string;
    enabled: boolean;
    responsible_ids: number[];
    random_round: number;
    checklist: DutyChecklistItem[];
    meeting_id?: number | null;
    start_time?: string | null;
    end_time?: string | null;
  }) => Promise<void>;
}

const DEFAULT_TASKS: string[] = [
  '🪟 Lau kính',
  '💨 Quạt + Đổ rác',
  '🧹 Quét nhà',
  '🪑 Lau bàn',
  '👟 Xếp dép',
];

export const RandomDutyAssignmentModal: React.FC<RandomDutyAssignmentModalProps> = ({
  isOpen,
  onClose,
  teamId,
  teamName,
  dutyDate,
  meetingId,
  startTime,
  endTime,
  onConfirm,
}) => {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [candidateData, setCandidateData] = useState<DutyCandidatesResponse | null>(null);

  // Danh sách công việc động (Admin có thể thêm, sửa, xóa)
  const [tasks, setTasks] = useState<TaskAssignmentItem[]>([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [isSpinning, setIsSpinning] = useState(false);

  const primaryTeamId = useMemo(() => {
    if (Array.isArray(teamId)) return teamId[0];
    if (typeof teamId === 'number') return teamId;
    if (typeof teamId === 'string') return parseInt(teamId, 10);
    return null;
  }, [teamId]);

  // 1. Khi mở Modal: Nạp danh sách ứng viên và chuẩn bị 5 việc mặc định
  useEffect(() => {
    if (isOpen && primaryTeamId) {
      const initialTasks = DEFAULT_TASKS.map((t, index) => ({
        id: `task_${Date.now()}_${index}`,
        title: t,
        assignee_id: null,
        assignee_name: null,
      }));
      setTasks(initialTasks);
      setNewTaskTitle('');

      const fetchCandidates = async () => {
        setLoading(true);
        try {
          const res = await dutyService.getCandidates(Number(primaryTeamId));
          if (res.data) {
            setCandidateData(res.data);
            // Tự động quay ngẫu nhiên lần đầu cho tiện lợi
            executeRandomAssignment(initialTasks, res.data);
          }
        } catch (error: any) {
          console.error('Lỗi lấy danh sách ứng viên:', error);
          const errDetail =
            error.response?.data?.detail || error.response?.data?.message || '';
          message.error(
            `Không thể lấy danh sách thành viên của lớp này ${errDetail ? `(${errDetail})` : ''}`
          );
        } finally {
          setLoading(false);
        }
      };

      fetchCandidates();
    }
  }, [isOpen, primaryTeamId]);

  // 2. Thuật toán Random: Có bao nhiêu việc thì quay bấy nhiêu người
  const executeRandomAssignment = (
    currentTasks: TaskAssignmentItem[],
    data: DutyCandidatesResponse | null = candidateData
  ) => {
    if (!data || !data.all_members || data.all_members.length === 0) {
      message.warning('Lớp học này chưa có thành viên để phân công');
      return;
    }

    const taskCount = currentTasks.length;
    if (taskCount === 0) {
      message.warning('Chưa có đầu việc nào để phân công');
      return;
    }

    setIsSpinning(true);

    // Lấy danh sách bạn chưa trực vòng này
    let pool = [...(data.available_members || [])];
    const all = [...(data.all_members || [])];

    // Trộn ngẫu nhiên (Fisher-Yates shuffle)
    const shuffle = (array: TeamCandidateMember[]) => {
      const arr = [...array];
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    };

    let selected: TeamCandidateMember[] = [];
    pool = shuffle(pool);

    if (pool.length >= taskCount) {
      // Đủ người trong vòng hiện tại
      selected = pool.slice(0, taskCount);
    } else {
      // Nếu số bạn chưa trực ít hơn số việc cần phân công -> lấy hết số bạn còn lại và sang vòng mới lấy thêm
      selected = [...pool];
      const remainingNeeded = taskCount - selected.length;
      const selectedIds = new Set(selected.map((s) => s.id));
      const restPool = shuffle(all.filter((m) => !selectedIds.has(m.id)));
      selected = [...selected, ...restPool.slice(0, remainingNeeded)];
    }

    // Gán 1 người cho 1 việc
    const updatedTasks = currentTasks.map((task, idx) => {
      const person = selected[idx];
      return {
        ...task,
        assignee_id: person ? person.id : null,
        assignee_name: person ? person.name : null,
      };
    });

    setTimeout(() => {
      setTasks(updatedTasks);
      setIsSpinning(false);
      message.success(`Đã quay ngẫu nhiên ${selected.length} bạn cho ${taskCount} công việc!`);
    }, 300);
  };

  // 3. Đổi người thủ công cho một công việc
  const handleAssigneeChange = (taskId: string, userId: number) => {
    const member = candidateData?.all_members.find((m) => m.id === userId);
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? {
            ...t,
            assignee_id: userId,
            assignee_name: member?.name || `Thành viên #${userId}`,
          }
          : t
      )
    );
  };

  // 4. Thêm công việc mới
  const handleAddTask = () => {
    if (!newTaskTitle.trim()) return;
    const newTask: TaskAssignmentItem = {
      id: `task_${Date.now()}`,
      title: newTaskTitle.trim(),
      assignee_id: null,
      assignee_name: null,
    };
    const updated = [...tasks, newTask];
    setTasks(updated);
    setNewTaskTitle('');
    // Nếu có danh sách ứng viên, tự động chọn thêm 1 bạn chưa được phân vào việc mới
    if (candidateData?.all_members) {
      const usedIds = new Set(updated.map((t) => t.assignee_id).filter(Boolean));
      const unused = candidateData.all_members.filter((m) => !usedIds.has(m.id));
      if (unused.length > 0) {
        const randomPerson = unused[Math.floor(Math.random() * unused.length)];
        newTask.assignee_id = randomPerson.id;
        newTask.assignee_name = randomPerson.name;
        setTasks([...updated]);
      }
    }
  };

  // 5. Xóa bớt công việc
  const handleDeleteTask = (taskId: string) => {
    if (tasks.length <= 1) {
      message.warning('Cần tối thiểu ít nhất 1 nhiệm vụ trực nhật');
      return;
    }
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  };

  // 6. Chốt và tạo lịch trực
  const handleConfirmSchedule = async () => {
    const unassignedTasks = tasks.filter((t) => !t.assignee_id);
    if (unassignedTasks.length > 0) {
      message.warning('Vui lòng phân công người phụ trách cho toàn bộ các công việc');
      return;
    }

    const responsibleIds = Array.from(
      new Set(tasks.map((t) => t.assignee_id).filter(Boolean) as number[])
    );

    const checklist: DutyChecklistItem[] = tasks.map((t) => ({
      id: t.id,
      title: t.title,
      checked: false,
      assignee_id: t.assignee_id,
      assignee_name: t.assignee_name,
    }));

    setSubmitting(true);
    try {
      await onConfirm({
        team_id: teamId,
        duty_date: dutyDate,
        enabled: true,
        responsible_ids: responsibleIds,
        random_round: candidateData?.current_round || 1,
        checklist,
        meeting_id: meetingId,
        start_time: startTime,
        end_time: endTime,
      });
      message.success('Đã chốt lịch trực và gửi thông báo thành công!');
      onClose();
    } catch (err: any) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const allMembers = candidateData?.all_members || [];

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      width={720}
      title={
        <div className="flex items-center gap-2 text-indigo-700">
          <TrophyOutlined className="text-xl" />
          <span className="text-lg font-bold">
            Phân công trực nhật: {teamName} - {dayjs(dutyDate).format('DD/MM/YYYY')}
          </span>
        </div>
      }
      footer={[
        <Button key="cancel" onClick={onClose} disabled={submitting}>
          Hủy
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={submitting}
          onClick={handleConfirmSchedule}
          icon={<CheckCircleOutlined />}
          className="bg-indigo-600 hover:bg-indigo-500 font-semibold px-5"
        >
          Xác nhận & Bật lịch trực
        </Button>,
      ]}
    >
      <Spin spinning={loading}>
        {/* Banner Vòng quay & Trạng thái thành viên */}
        <div className="bg-indigo-50/70 border border-indigo-100 rounded-xl p-3.5 mb-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Tag color="purple" className="font-semibold text-xs px-2.5 py-0.5 rounded-full">
                Vòng {candidateData?.current_round || 1}
              </Tag>
              <Text className="text-gray-700 text-sm font-medium">
                {candidateData?.available_members?.length || 0} / {candidateData?.total_members || 0} bạn chưa trực vòng này
              </Text>
            </div>
            <Button
              type="primary"
              size="middle"
              icon={<ReloadOutlined spin={isSpinning} />}
              onClick={() => executeRandomAssignment(tasks)}
              disabled={isSpinning || allMembers.length === 0}
              className="bg-emerald-600 hover:bg-emerald-500 font-medium rounded-lg text-xs"
            >
              🎲 Quay ngẫu nhiên ({tasks.length} bạn)
            </Button>
          </div>
          <Text type="secondary" className="text-xs block mt-1.5 text-gray-500">
            💡 Có bao nhiêu việc sẽ tự động quay bấy nhiêu người. Bạn có thể bấm chọn đổi bạn khác.
          </Text>
        </div>

        {/* Danh sách nhiệm vụ và người phụ trách tương ứng */}
        <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
          {tasks.map((task, index) => (
            <Card
              key={task.id}
              size="small"
              className="border border-gray-200 hover:border-indigo-300 transition-all shadow-sm rounded-xl"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                {/* Tên đầu việc */}
                <div className="flex items-center gap-2 flex-1">
                  <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                    {index + 1}
                  </span>
                  <Input
                    value={task.title}
                    onChange={(e) => {
                      const val = e.target.value;
                      setTasks((prev) =>
                        prev.map((t) => (t.id === task.id ? { ...t, title: val } : t))
                      );
                    }}
                    className="font-medium text-gray-800 rounded-lg"
                    placeholder="Tên đầu việc..."
                  />
                </div>

                {/* Dropdown chọn người phụ trách */}
                <div className="flex items-center gap-2 sm:w-64">
                  <Select
                    showSearch
                    optionFilterProp="label"
                    value={task.assignee_id || undefined}
                    onChange={(val) => handleAssigneeChange(task.id, val)}
                    placeholder="Chọn người phụ trách..."
                    className="w-full"
                    options={allMembers.map((m) => ({
                      value: m.id,
                      label: `${m.name}${m.served ? ' (Đã trực)' : ''}`,
                    }))}
                  />
                  {tasks.length > 1 && (
                    <Tooltip title="Xóa đầu việc này">
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteTask(task.id)}
                        className="flex-shrink-0"
                      />
                    </Tooltip>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Thêm đầu việc mới */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-2">
          <Input
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            onPressEnter={handleAddTask}
            placeholder="Nhập thêm đầu việc mới (ví dụ: Lau bảng, sắp xếp bàn ghế)..."
            className="rounded-lg"
          />
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={handleAddTask}
            disabled={!newTaskTitle.trim()}
            className="rounded-lg"
          >
            Thêm việc
          </Button>
        </div>
      </Spin>
    </Modal>
  );
};
