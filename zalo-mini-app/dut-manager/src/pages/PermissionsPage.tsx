import React from 'react';
import { Page } from 'zmp-ui';
import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import {
  PermissionHeader,
  PermissionFilters,
  PermissionList,
  PermissionFormModal,
  PermissionDetailModal,
  PermissionDeleteModal,
  usePermissionManagement,
  formatDate,
} from '@/features/permission_request';

const PermissionsPage: React.FC = () => {
  const { user, isAuthenticated, hasPermission } = useAuth();

  const {
    permissions,
    meetings,
    homeworks,
    isLoading,
    selectedCategory,
    setSelectedCategory,
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
    isSubmitting,
    isDeleting,
    openCreateModal,
    openEditModal,
    closeModal,
    handleFormSubmit,
    confirmDelete,
  } = usePermissionManagement(isAuthenticated);

  const hasUpdatePermission = hasPermission('permissions:update');
  const hasDeletePermission = hasPermission('permissions:delete');

  return (
    <Page className="bg-[#f8fafc] flex flex-col min-h-screen">
      <Header title="Quản lý Đơn xin phép" showBack={true} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-3 pb-24">
        {/* 1. Header Card (Total count & Add button) */}
        <PermissionHeader
          total={permissions.length}
          onOpenCreate={openCreateModal}
        />

        {/* 2. Category Filters */}
        <PermissionFilters
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />

        {/* 3. Permission List / Empty State / Cards */}
        <PermissionList
          permissions={permissions}
          isLoading={isLoading}
          currentUserId={user?.id}
          hasDeletePermission={hasDeletePermission}
          hasUpdatePermission={hasUpdatePermission}
          onOpenCreate={openCreateModal}
          onViewDetail={(item) => setDetailItem(item)}
          onEdit={(item) => openEditModal(item)}
          onDelete={(id) => setDeletingId(id)}
        />
      </div>

      {/* 4. Form Modal (Create / Edit) */}
      <PermissionFormModal
        isOpen={isModalOpen}
        editingItem={editingItem}
        formCategory={formCategory}
        formMeetingId={formMeetingId}
        formHomeworkId={formHomeworkId}
        formStartTime={formStartTime}
        formLateTime={formLateTime}
        formNote={formNote}
        meetings={meetings}
        homeworks={homeworks}
        isSubmitting={isSubmitting}
        onClose={closeModal}
        onSubmit={handleFormSubmit}
        setFormCategory={setFormCategory}
        setFormMeetingId={setFormMeetingId}
        setFormHomeworkId={setFormHomeworkId}
        setFormStartTime={setFormStartTime}
        setFormLateTime={setFormLateTime}
        setFormNote={setFormNote}
        formatDate={formatDate}
      />

      {/* 5. Detail Modal */}
      <PermissionDetailModal
        item={detailItem}
        currentUserId={user?.id}
        hasUpdatePermission={hasUpdatePermission}
        onClose={() => setDetailItem(null)}
        onOpenEdit={(item) => openEditModal(item)}
        formatDate={formatDate}
      />

      {/* 6. Delete Confirmation Modal */}
      <PermissionDeleteModal
        deletingId={deletingId}
        isDeleting={isDeleting}
        onClose={() => setDeletingId(null)}
        onConfirm={confirmDelete}
      />
    </Page>
  );
};

export default PermissionsPage;


