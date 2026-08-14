import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'zmp-ui';
import { permissionService } from '@/services/api/permission.service';
import { meetingService, type MeetingItem } from '@/services/api/meeting.service';
import { homeworkService, type HomeworkItem } from '@/services/api/homework.service';
import {
  RequestCategory,
  PermissionRequestResponse,
  PermissionRequestCreate,
  PermissionRequestUpdate,
} from '@/types/permission.types';

export const usePermissionManagement = (isAuthenticated: boolean) => {
  const queryClient = useQueryClient();
  const { openSnackbar } = useSnackbar();

  // Filters State
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [filterMonth, setFilterMonth] = useState<number | undefined>(undefined);
  const [filterYear, setFilterYear] = useState<number | undefined>(undefined);

  // Modals & Details State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<PermissionRequestResponse | null>(null);
  const [detailItem, setDetailItem] = useState<PermissionRequestResponse | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Form State
  const [formCategory, setFormCategory] = useState<RequestCategory>(RequestCategory.ABSENCE);
  const [formMeetingId, setFormMeetingId] = useState<number | undefined>(undefined);
  const [formHomeworkId, setFormHomeworkId] = useState<number | undefined>(undefined);
  const [formStartTime, setFormStartTime] = useState<string>('');
  const [formLateTime, setFormLateTime] = useState<string>('19:30');
  const [formNote, setFormNote] = useState<string>('');

  // 1. Fetch Permissions
  const {
    data: permissions = [],
    isLoading,
    refetch,
  } = useQuery<PermissionRequestResponse[]>({
    queryKey: ['permissions', selectedCategory, filterMonth, filterYear],
    queryFn: async () => {
      const categoryParam = selectedCategory === 'ALL' ? undefined : selectedCategory;
      return await permissionService.getPermissions({
        category: categoryParam,
        month: filterMonth,
        year: filterYear,
      });
    },
    enabled: isAuthenticated,
  });

  // 2. Fetch Meetings & Homeworks
  const { data: meetings = [] } = useQuery<MeetingItem[]>({
    queryKey: ['meetings-lookup'],
    queryFn: async () => await meetingService.getMeetings(0, 50),
    enabled: isAuthenticated,
  });

  const { data: homeworks = [] } = useQuery<HomeworkItem[]>({
    queryKey: ['homeworks-lookup'],
    queryFn: async () => await homeworkService.getAll(0, 50),
    enabled: isAuthenticated,
  });

  // 3. Create Mutation
  const createMutation = useMutation({
    mutationFn: (data: PermissionRequestCreate) => permissionService.createPermission(data),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Tạo đơn xin phép thành công!', type: 'success' });
        closeModal();
        queryClient.invalidateQueries({ queryKey: ['permissions'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể tạo đơn', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  // 4. Update Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PermissionRequestUpdate }) =>
      permissionService.updatePermission(id, data),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Cập nhật đơn xin phép thành công!', type: 'success' });
        closeModal();
        if (detailItem && editingItem && detailItem.id === editingItem.id) {
          setDetailItem(null);
        }
        queryClient.invalidateQueries({ queryKey: ['permissions'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể cập nhật đơn', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  // 5. Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => permissionService.deletePermission(id),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Đã xóa đơn xin phép', type: 'success' });
        setDeletingId(null);
        if (detailItem && detailItem.id === deletingId) {
          setDetailItem(null);
        }
        queryClient.invalidateQueries({ queryKey: ['permissions'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể xóa đơn', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  const openCreateModal = () => {
    setEditingItem(null);
    setFormCategory(RequestCategory.ABSENCE);
    setFormMeetingId(meetings.length > 0 ? meetings[0].id : undefined);
    setFormHomeworkId(homeworks.length > 0 ? homeworks[0].id : undefined);
    setFormStartTime('');
    setFormLateTime('19:30');
    setFormNote('');
    setIsModalOpen(true);
  };

  const openEditModal = (item: PermissionRequestResponse) => {
    setEditingItem(item);
    setFormCategory(item.category as RequestCategory);
    setFormMeetingId(item.meeting_id || (item.meeting?.id ?? undefined));
    setFormHomeworkId(item.homework_id || (item.homework?.id ?? undefined));
    setFormNote(item.note || '');

    if (item.start_time) {
      if (item.category === 'LATE') {
        const d = new Date(item.start_time);
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        setFormLateTime(`${hh}:${mm}`);
      } else {
        const d = new Date(item.start_time);
        const iso = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16);
        setFormStartTime(iso);
      }
    } else {
      setFormStartTime('');
      setFormLateTime('19:30');
    }

    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingItem(null);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formNote.trim()) {
      openSnackbar({ text: 'Vui lòng nhập lý do xin phép cụ thể', type: 'warning' });
      return;
    }

    let finalStartTime: string | undefined = undefined;

    if (formCategory === RequestCategory.POSTPONE) {
      if (!formHomeworkId) {
        openSnackbar({ text: 'Vui lòng chọn bài tập cần xin hoãn!', type: 'warning' });
        return;
      }
      if (!formStartTime) {
        openSnackbar({ text: 'Vui lòng chọn hạn nộp mới (deadline)!', type: 'warning' });
        return;
      }

      const selectedHw = homeworks.find((h) => h.id === formHomeworkId);
      if (selectedHw && selectedHw.deadline) {
        const originDeadline = new Date(selectedHw.deadline).getTime();
        const newDeadline = new Date(formStartTime).getTime();
        const diffDays = (newDeadline - originDeadline) / (1000 * 60 * 60 * 24);

        if (diffDays < 0) {
          openSnackbar({ text: 'Hạn mới phải sau hạn nộp gốc của bài tập!', type: 'warning' });
          return;
        }
        if (diffDays > 4) {
          openSnackbar({
            text: 'Thời gian xin hoãn không được vượt quá 4 ngày so với deadline gốc!',
            type: 'warning',
          });
          return;
        }
      }

      finalStartTime = new Date(formStartTime).toISOString();
    } else if (formCategory === RequestCategory.LATE) {
      if (!formMeetingId) {
        openSnackbar({ text: 'Vui lòng chọn buổi sinh hoạt / họp!', type: 'warning' });
        return;
      }
      const selectedMeet = meetings.find((m) => m.id === formMeetingId);
      if (selectedMeet && selectedMeet.start_time) {
        const meetDate = new Date(selectedMeet.start_time);
        const [hh, mm] = formLateTime.split(':').map(Number);
        meetDate.setHours(hh || 19, mm || 30, 0, 0);
        finalStartTime = meetDate.toISOString();
      } else {
        finalStartTime = new Date().toISOString();
      }
    } else if (formCategory === RequestCategory.ABSENCE) {
      if (!formMeetingId) {
        openSnackbar({ text: 'Vui lòng chọn buổi sinh hoạt / họp!', type: 'warning' });
        return;
      }
      const selectedMeet = meetings.find((m) => m.id === formMeetingId);
      finalStartTime = selectedMeet?.start_time || undefined;
    }

    const payload = {
      category: formCategory,
      note: formNote.trim(),
      start_time: finalStartTime,
      meeting_id:
        formCategory === RequestCategory.ABSENCE || formCategory === RequestCategory.LATE
          ? formMeetingId
          : undefined,
      homework_id: formCategory === RequestCategory.POSTPONE ? formHomeworkId : undefined,
    };

    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  return {
    permissions,
    meetings,
    homeworks,
    isLoading,
    refetch,
    selectedCategory,
    setSelectedCategory,
    filterMonth,
    setFilterMonth,
    filterYear,
    setFilterYear,
    isModalOpen,
    editingItem,
    detailItem,
    setDetailItem,
    deletingId,
    setDeletingId,
    formCategory,
    setFormCategory,
    formMeetingId,
    setFormMeetingId,
    formHomeworkId,
    setFormHomeworkId,
    formStartTime,
    setFormStartTime,
    formLateTime,
    setFormLateTime,
    formNote,
    setFormNote,
    isSubmitting: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    openCreateModal,
    openEditModal,
    closeModal,
    handleFormSubmit,
    confirmDelete: () => deletingId && deleteMutation.mutate(deletingId),
  };
};
