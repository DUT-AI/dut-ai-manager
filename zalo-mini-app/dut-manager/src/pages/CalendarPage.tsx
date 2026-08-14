import React from 'react';
import { Page, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import {
  MeetingCalendarHeader,
  ZaloMobileCalendar,
  MeetingList,
  MeetingFormModal,
  MeetingDetailModal,
  MeetingDeleteModal,
  useMeetingCalendar,
} from '@/features/schedule';
import { formatDateFull } from '@/features/schedule/MeetingCard';

const CalendarPage: React.FC = () => {
  const { user, isAuthenticated, hasPermission } = useAuth();

  const {
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
    isSubmitting,
    isDeleting,
    goToPrevWeek,
    goToNextWeek,
    goToToday,
    openCreateModal,
    openEditModal,
    closeModal,
    handleFormSubmit,
    confirmDelete,
  } = useMeetingCalendar(isAuthenticated);

  const canCreate = hasPermission('meetings:create');
  const hasUpdatePermission = hasPermission('meetings:update');
  const hasDeletePermission = hasPermission('meetings:delete');

  return (
    <Page className="bg-[#f8fafc] flex flex-col min-h-screen">
      <Header title="Lịch Meeting" showBack={false} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-3 pb-24">
        {/* 1. Header with Add Meeting Button & View Switcher */}
        <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center justify-between">
          <div className="flex flex-col">
            <h2 className="font-bold text-base text-gray-900">Lịch Họp & Sinh hoạt</h2>
            <p className="text-xs text-gray-500">
              Tổng cộng: <strong className="text-blue-600 font-semibold">{meetings.length}</strong> cuộc họp
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* View Switcher: Calendar Month vs Weekly List */}
            <div className="flex bg-gray-100 p-1 rounded-xl">
              <button
                onClick={() => setViewMode('calendar')}
                className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                  viewMode === 'calendar'
                    ? 'bg-white text-blue-600 shadow-xs'
                    : 'text-gray-500'
                }`}
                title="Xem theo Lịch tháng"
              >
                <Icon icon="zi-calendar" size={16} />
              </button>
              <button
                onClick={() => setViewMode('week')}
                className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                  viewMode === 'week'
                    ? 'bg-white text-blue-600 shadow-xs'
                    : 'text-gray-500'
                }`}
                title="Xem theo Tuần"
              >
                <Icon icon="zi-list-1" size={16} />
              </button>
            </div>

            {canCreate && (
              <button
                onClick={openCreateModal}
                className="bg-blue-600 text-white p-2 rounded-xl text-xs font-bold flex items-center gap-1 shadow-xs active:bg-blue-700"
              >
                <Icon icon="zi-plus" size={16} />
                <span className="hidden sm:inline">Tạo mới</span>
              </button>
            )}
          </div>
        </div>

        {/* 2. Zalo UI Mobile Calendar (Interactive Month Grid) */}
        {viewMode === 'calendar' && (
          <div className="flex flex-col gap-2">
            <ZaloMobileCalendar
              selectedDate={selectedDate}
              meetings={meetings}
              onSelectDate={(date) => setSelectedDate(date)}
            />

            {/* Selected Date Header */}
            <div className="flex items-center justify-between px-1 pt-1">
              <span className="text-xs font-bold text-gray-800">
                Cuộc họp ngày: <span className="text-blue-600">{formatDateFull(selectedDate.toISOString())}</span>
              </span>
              <span className="text-xs text-gray-500">
                {filteredMeetings.length} cuộc họp
              </span>
            </div>
          </div>
        )}

        {/* 3. Weekly Navigation Header (when in Week mode) */}
        {viewMode === 'week' && (
          <MeetingCalendarHeader
            currentWeekLabel={currentWeekLabel}
            totalMeetings={filteredMeetings.length}
            isCurrentWeek={isCurrentWeek}
            canCreate={false}
            onPrevWeek={goToPrevWeek}
            onNextWeek={goToNextWeek}
            onToday={goToToday}
            onOpenCreate={openCreateModal}
          />
        )}

        {/* 4. Meetings List */}
        <MeetingList
          meetings={filteredMeetings}
          isLoading={isLoading}
          currentUserId={user?.id}
          hasUpdatePermission={hasUpdatePermission}
          hasDeletePermission={hasDeletePermission}
          canCreate={canCreate}
          onOpenCreate={openCreateModal}
          onSelectMeeting={(m) => setDetailItem(m)}
          onEditMeeting={(m) => openEditModal(m)}
          onDeleteMeeting={(id) => setDeletingId(id)}
        />
      </div>

      {/* 5. Modal Tạo / Chỉnh sửa Meeting */}
      <MeetingFormModal
        isOpen={isModalOpen}
        editingItem={editingItem}
        formTitle={formTitle}
        formContent={formContent}
        formStartTime={formStartTime}
        formEndTime={formEndTime}
        formRequireCheckIn={formRequireCheckIn}
        formUserIds={formUserIds}
        formTeamIds={formTeamIds}
        users={users}
        teams={teams}
        isSubmitting={isSubmitting}
        onClose={closeModal}
        onSubmit={handleFormSubmit}
        setFormTitle={setFormTitle}
        setFormContent={setFormContent}
        setFormStartTime={setFormStartTime}
        setFormEndTime={setFormEndTime}
        setFormRequireCheckIn={setFormRequireCheckIn}
        toggleUserId={toggleUserId}
        toggleTeamId={toggleTeamId}
      />

      {/* 6. Modal Chi tiết Meeting & Điểm danh Checkin */}
      <MeetingDetailModal
        meeting={detailItem}
        currentUserId={user?.id}
        hasUpdatePermission={hasUpdatePermission}
        hasDeletePermission={hasDeletePermission}
        onClose={() => setDetailItem(null)}
        onOpenEdit={(m) => openEditModal(m)}
        onDelete={(id) => setDeletingId(id)}
        onRefetch={refetch}
      />

      {/* 7. Modal Xác nhận Xóa Meeting */}
      <MeetingDeleteModal
        deletingId={deletingId}
        isDeleting={isDeleting}
        onClose={() => setDeletingId(null)}
        onConfirm={confirmDelete}
      />
    </Page>
  );
};

export default CalendarPage;
