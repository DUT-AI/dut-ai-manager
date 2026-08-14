import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'zmp-ui';
import { meetingService } from '@/services/api/meeting.service';
import { userService, type UserSummary } from '@/services/api/user.service';
import { teamService, type TeamSummary } from '@/services/api/team.service';
import type {
  MeetingResponse,
  MeetingCreate,
  MeetingUpdate,
} from '@/types/meeting.types';

// Helper for getting start of week (Monday)
const getStartOfWeek = (date: Date): Date => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
};

export const useMeetingCalendar = (isAuthenticated: boolean) => {
  const queryClient = useQueryClient();
  const { openSnackbar } = useSnackbar();

  // Selected date for calendar view & active week
  const [selectedDate, setSelectedDate] = useState<Date>(() => new Date());
  const [viewMode, setViewMode] = useState<'calendar' | 'week'>('calendar');

  const currentWeekStart = useMemo(() => getStartOfWeek(selectedDate), [selectedDate]);

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<MeetingResponse | null>(null);
  const [detailItem, setDetailItem] = useState<MeetingResponse | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Form State
  const [formTitle, setFormTitle] = useState<string>('');
  const [formContent, setFormContent] = useState<string>('');
  const [formStartTime, setFormStartTime] = useState<string>('');
  const [formEndTime, setFormEndTime] = useState<string>('');
  const [formRequireCheckIn, setFormRequireCheckIn] = useState<boolean>(true);
  const [formUserIds, setFormUserIds] = useState<number[]>([]);
  const [formTeamIds, setFormTeamIds] = useState<number[]>([]);

  // Calculate month and week range strings for data fetching
  const { startDateStr, endDateStr } = useMemo(() => {
    // Fetch +/- 45 days around selected date to ensure smooth calendar browsing
    const start = new Date(selectedDate);
    start.setDate(start.getDate() - 35);
    const end = new Date(selectedDate);
    end.setDate(end.getDate() + 35);
    return {
      startDateStr: start.toISOString().slice(0, 10),
      endDateStr: end.toISOString().slice(0, 10),
    };
  }, [selectedDate]);

  const weekEnd = useMemo(() => {
    const d = new Date(currentWeekStart);
    d.setDate(d.getDate() + 6);
    return d;
  }, [currentWeekStart]);

  const currentWeekLabel = useMemo(() => {
    const s = `${currentWeekStart.getDate()}/${currentWeekStart.getMonth() + 1}`;
    const e = `${weekEnd.getDate()}/${weekEnd.getMonth() + 1}/${weekEnd.getFullYear()}`;
    return `${s} – ${e}`;
  }, [currentWeekStart, weekEnd]);

  const isCurrentWeek = useMemo(() => {
    const todayWeekStart = getStartOfWeek(new Date());
    return currentWeekStart.getTime() === todayWeekStart.getTime();
  }, [currentWeekStart]);

  // 1. Fetch Meetings
  const {
    data: meetings = [],
    isLoading,
    refetch,
  } = useQuery<MeetingResponse[]>({
    queryKey: ['meetings-calendar', startDateStr, endDateStr],
    queryFn: async () => {
      return await meetingService.getMeetingsByDateRange(startDateStr, endDateStr);
    },
    enabled: isAuthenticated,
  });

  // Filter meetings for the currently selected date or current week
  const filteredMeetings = useMemo(() => {
    if (viewMode === 'calendar') {
      const targetStr = selectedDate.toISOString().slice(0, 10);
      return meetings.filter((m) => m.start_time.slice(0, 10) === targetStr);
    } else {
      const wStart = currentWeekStart.getTime();
      const wEnd = new Date(weekEnd).setHours(23, 59, 59, 999);
      return meetings.filter((m) => {
        const mTime = new Date(m.start_time).getTime();
        return mTime >= wStart && mTime <= wEnd;
      });
    }
  }, [meetings, viewMode, selectedDate, currentWeekStart, weekEnd]);

  // 2. Fetch Users & Teams for selector
  const { data: users = [] } = useQuery<UserSummary[]>({
    queryKey: ['users-lookup'],
    queryFn: async () => await userService.getUsers(),
    enabled: isAuthenticated,
  });

  const { data: teams = [] } = useQuery<TeamSummary[]>({
    queryKey: ['teams-lookup'],
    queryFn: async () => await teamService.getTeams(0, 100),
    enabled: isAuthenticated,
  });

  // 3. Create Meeting Mutation
  const createMutation = useMutation({
    mutationFn: (data: MeetingCreate) => meetingService.createMeeting(data),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Tạo cuộc họp thành công!', type: 'success' });
        closeModal();
        queryClient.invalidateQueries({ queryKey: ['meetings-calendar'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể tạo cuộc họp', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  // 4. Update Meeting Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: MeetingUpdate }) =>
      meetingService.updateMeeting(id, data),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Cập nhật cuộc họp thành công!', type: 'success' });
        closeModal();
        if (detailItem && editingItem && detailItem.id === editingItem.id) {
          setDetailItem(null);
        }
        queryClient.invalidateQueries({ queryKey: ['meetings-calendar'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể cập nhật cuộc họp', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  // 5. Delete Meeting Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => meetingService.deleteMeeting(id),
    onSuccess: (res) => {
      if (res.is_success) {
        openSnackbar({ text: 'Đã xóa cuộc họp', type: 'success' });
        setDeletingId(null);
        if (detailItem && detailItem.id === deletingId) {
          setDetailItem(null);
        }
        queryClient.invalidateQueries({ queryKey: ['meetings-calendar'] });
      } else {
        openSnackbar({ text: res.message || 'Không thể xóa cuộc họp', type: 'error' });
      }
    },
    onError: (err: any) => {
      openSnackbar({ text: err?.message || 'Có lỗi xảy ra', type: 'error' });
    },
  });

  const goToPrevWeek = () => {
    const prev = new Date(selectedDate);
    prev.setDate(prev.getDate() - 7);
    setSelectedDate(prev);
  };

  const goToNextWeek = () => {
    const next = new Date(selectedDate);
    next.setDate(next.getDate() + 7);
    setSelectedDate(next);
  };

  const goToToday = () => {
    setSelectedDate(new Date());
  };

  const openCreateModal = () => {
    setEditingItem(null);
    setFormTitle('');
    setFormContent('');

    // Default: Selected date at 19:30 to 21:00
    const dStart = new Date(selectedDate);
    dStart.setHours(19, 30, 0, 0);
    const dEnd = new Date(selectedDate);
    dEnd.setHours(21, 0, 0, 0);

    const toLocalISO = (d: Date) =>
      new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

    setFormStartTime(toLocalISO(dStart));
    setFormEndTime(toLocalISO(dEnd));
    setFormRequireCheckIn(true);
    setFormUserIds([]);
    setFormTeamIds([]);
    setIsModalOpen(true);
  };

  const openEditModal = (meeting: MeetingResponse) => {
    setEditingItem(meeting);
    setFormTitle(meeting.title);
    setFormContent(meeting.content || '');
    setFormRequireCheckIn(meeting.require_check_in);

    const toLocalISO = (isoStr: string) => {
      const d = new Date(isoStr);
      return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    };

    setFormStartTime(toLocalISO(meeting.start_time));
    setFormEndTime(toLocalISO(meeting.end_time));
    setFormUserIds(meeting.participants?.map((p) => p.user_id) || []);
    setFormTeamIds([]);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingItem(null);
  };

  const toggleUserId = (id: number) => {
    setFormUserIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleTeamId = (id: number) => {
    setFormTeamIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formTitle.trim()) {
      openSnackbar({ text: 'Vui lòng nhập tiêu đề cuộc họp', type: 'warning' });
      return;
    }

    if (!formStartTime || !formEndTime) {
      openSnackbar({ text: 'Vui lòng chọn thời gian bắt đầu và kết thúc', type: 'warning' });
      return;
    }

    if (new Date(formStartTime) >= new Date(formEndTime)) {
      openSnackbar({ text: 'Thời gian kết thúc phải sau thời gian bắt đầu', type: 'warning' });
      return;
    }

    const payload = {
      title: formTitle.trim(),
      content: formContent.trim() || undefined,
      start_time: new Date(formStartTime).toISOString(),
      end_time: new Date(formEndTime).toISOString(),
      require_check_in: formRequireCheckIn,
      user_ids: formUserIds.length > 0 ? formUserIds : undefined,
      team_ids: formTeamIds.length > 0 ? formTeamIds : undefined,
    };

    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  return {
    meetings,
    filteredMeetings,
    selectedDate,
    setSelectedDate,
    viewMode,
    setViewMode,
    users,
    teams,
    isLoading,
    refetch,
    currentWeekLabel,
    isCurrentWeek,
    isModalOpen,
    editingItem,
    detailItem,
    setDetailItem,
    deletingId,
    setDeletingId,
    formTitle,
    setFormTitle,
    formContent,
    setFormContent,
    formStartTime,
    setFormStartTime,
    formEndTime,
    setFormEndTime,
    formRequireCheckIn,
    setFormRequireCheckIn,
    formUserIds,
    formTeamIds,
    toggleUserId,
    toggleTeamId,
    isSubmitting: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    goToPrevWeek,
    goToNextWeek,
    goToToday,
    openCreateModal,
    openEditModal,
    closeModal,
    handleFormSubmit,
    confirmDelete: () => deletingId && deleteMutation.mutate(deletingId),
  };
};
