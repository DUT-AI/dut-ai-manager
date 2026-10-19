import { useState, useCallback, useEffect } from 'react';
import { message } from 'antd';
import { dutyService } from '../services/duty.service';
import type { DutyResponse, WeeklyDutyClassDto } from '../types/duty.types';

export const useDutyManagement = () => {
  const [weeklySchedule, setWeeklySchedule] = useState<WeeklyDutyClassDto[]>([]);
  const [loadingWeekly, setLoadingWeekly] = useState(false);

  const [duties, setDuties] = useState<DutyResponse[]>([]);
  const [totalDuties, setTotalDuties] = useState(0);
  const [loadingDuties, setLoadingDuties] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [selectedDuty, setSelectedDuty] = useState<DutyResponse | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [targetDutyIdForSubmit, setTargetDutyIdForSubmit] = useState<number | null>(null);

  const fetchWeeklySchedule = useCallback(async (targetDate?: string) => {
    try {
      setLoadingWeekly(true);
      const res = await dutyService.getWeeklySchedule(targetDate);
      if (res.data) {
        setWeeklySchedule(res.data);
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Không thể tải lịch trực tuần');
    } finally {
      setLoadingWeekly(false);
    }
  }, []);

  const fetchDuties = useCallback(
    async (params?: { page?: number; page_size?: number; status?: string }) => {
      try {
        setLoadingDuties(true);
        const currentPage = params?.page ?? page;
        const currentPageSize = params?.page_size ?? pageSize;
        const res = await dutyService.getDuties({
          page: currentPage,
          page_size: currentPageSize,
          status: params?.status,
        });
        if (res.data) {
          setDuties(res.data);
          setTotalDuties(res.pagination?.total || 0);
        }
      } catch (err: any) {
        message.error(err.response?.data?.message || 'Không thể tải danh sách ca trực');
      } finally {
        setLoadingDuties(false);
      }
    },
    [page, pageSize]
  );

  const toggleSchedule = async (
    teamId: number | number[],
    dutyDate: string,
    enabled: boolean,
    options?: {
      meeting_id?: number | null;
      start_time?: string | null;
      end_time?: string | null;
      checklist?: DutyChecklistItem[];
      note?: string | null;
    }
  ) => {
    try {
      await dutyService.toggleSchedule({
        team_id: teamId,
        duty_date: dutyDate,
        enabled,
        ...options,
      });
      message.success(enabled ? 'Đã lên lịch trực nhật thành công' : 'Đã hủy ca trực nhật');
      fetchWeeklySchedule();
      fetchDuties();
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Thao tác thất bại';
      message.error(errMsg);
      throw err;
    }
  };

  const batchCreateDuties = async (data: import('../types/duty.types').BatchCreateDutyRequest) => {
    try {
      const res = await dutyService.batchCreateDuties(data);
      message.success(`Đã tạo thành công ${res.data?.length || 1} ca trực nhật`);
      fetchWeeklySchedule();
      fetchDuties();
      return res.data;
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Thao tác thất bại';
      message.error(errMsg);
      throw err;
    }
  };

  const updateDuty = async (
    dutyId: number,
    data: import('../types/duty.types').UpdateDutyRequest
  ) => {
    try {
      await dutyService.updateDuty(dutyId, data);
      message.success('Cập nhật ca trực nhật thành công');
      fetchWeeklySchedule();
      fetchDuties();
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Cập nhật ca trực thất bại';
      message.error(errMsg);
      throw err;
    }
  };

  const deleteDuty = async (dutyId: number) => {
    try {
      await dutyService.deleteDuty(dutyId);
      message.success('Đã hủy/xóa ca trực nhật thành công');
      fetchWeeklySchedule();
      fetchDuties();
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Xóa ca trực thất bại';
      message.error(errMsg);
      throw err;
    }
  };

  const restoreDuty = async (dutyId: number) => {
    try {
      await dutyService.restoreDuty(dutyId);
      message.success('Đã hồi phục ca trực nhật thành công');
      fetchWeeklySchedule();
      fetchDuties();
    } catch (err: any) {
      const errMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Hồi phục ca trực thất bại';
      message.error(errMsg);
      throw err;
    }
  };

  const openSubmitModal = (dutyId: number) => {
    setTargetDutyIdForSubmit(dutyId);
    setIsSubmitModalOpen(true);
  };

  const openDetailModal = async (dutyId: number) => {
    try {
      const res = await dutyService.getDutyById(dutyId);
      if (res.data) {
        setSelectedDuty(res.data);
        setIsDetailModalOpen(true);
      }
    } catch (err: any) {
      message.error('Không thể tải chi tiết ca trực');
    }
  };

  const approveDuty = async (dutyId: number) => {
    try {
      await dutyService.approveDuty(dutyId);
      message.success('Đã duyệt ca trực nhật thành công (Chuyển thành ĐÃ HOÀN THÀNH)');
      fetchWeeklySchedule();
      fetchDuties();
      if (selectedDuty?.id === dutyId) {
        setIsDetailModalOpen(false);
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Không thể duyệt ca trực');
    }
  };

  const rejectDuty = async (dutyId: number, reason: string) => {
    try {
      await dutyService.rejectDuty(dutyId, reason);
      message.warning('Đã từ chối minh chứng ca trực (Học viên cần vệ sinh và nộp lại)');
      fetchWeeklySchedule();
      fetchDuties();
      if (selectedDuty?.id === dutyId) {
        setIsDetailModalOpen(false);
      }
    } catch (err: any) {
      message.error(err.response?.data?.message || 'Không thể từ chối ca trực');
    }
  };

  useEffect(() => {
    fetchWeeklySchedule();
    fetchDuties();
  }, [fetchWeeklySchedule, fetchDuties]);

  return {
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
    batchCreateDuties,
    selectedDuty,
    setSelectedDuty,
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
  };
};
