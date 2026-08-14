import React from 'react';
import { Page, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useNavigate } from 'react-router-dom';
import { navigateForward } from '@/utils/navigation';
import { PATHS } from '@/constants/paths';

interface ShortcutItem {
  id: string;
  title: string;
  icon: string;
  color: string;
  bg: string;
  path: string;
}

const ShortcutsPage: React.FC = () => {
  const navigate = useNavigate();

  const memberShortcuts: ShortcutItem[] = [
    { id: '1', title: 'BC Học tập', icon: 'zi-file-text', color: 'text-blue-600', bg: 'bg-blue-50', path: PATHS.ACADEMIC_REPORTS },
    { id: '2', title: 'BC Hoạt động', icon: 'zi-check-circle', color: 'text-green-600', bg: 'bg-green-50', path: PATHS.ACTIVITY_REPORTS },
    { id: '3', title: 'Lịch hoạt động', icon: 'zi-calendar', color: 'text-cyan-600', bg: 'bg-cyan-50', path: PATHS.ACTIVITIES },
    { id: '4', title: 'Lịch Meeting', icon: 'zi-video', color: 'text-purple-600', bg: 'bg-purple-50', path: PATHS.MEETINGS },
    { id: '5', title: 'Đơn xin phép', icon: 'zi-note', color: 'text-rose-600', bg: 'bg-rose-50', path: PATHS.PERMISSIONS },
    { id: '6', title: 'Ghi vi phạm', icon: 'zi-warning', color: 'text-amber-600', bg: 'bg-amber-50', path: PATHS.VIOLATIONS },
    { id: '7', title: 'Bài tập lab', icon: 'zi-folder', color: 'text-indigo-600', bg: 'bg-indigo-50', path: PATHS.HOMEWORKS },
    { id: '8', title: 'Hóa đơn', icon: 'zi-wallet', color: 'text-emerald-600', bg: 'bg-emerald-50', path: PATHS.INVOICES },
  ];

  const adminShortcuts: ShortcutItem[] = [
    { id: '9', title: 'Thành viên', icon: 'zi-user', color: 'text-indigo-600', bg: 'bg-indigo-50', path: PATHS.USERS },
    { id: '10', title: 'Nhóm (Teams)', icon: 'zi-members', color: 'text-teal-600', bg: 'bg-teal-50', path: PATHS.TEAMS },
    { id: '11', title: 'Phân quyền', icon: 'zi-shield-check', color: 'text-violet-600', bg: 'bg-violet-50', path: PATHS.RBAC },
    { id: '12', title: 'Quản lý Quỹ', icon: 'zi-check-circle', color: 'text-pink-600', bg: 'bg-pink-50', path: PATHS.ADMIN_BILLING },
    { id: '13', title: 'Cài đặt', icon: 'zi-setting', color: 'text-gray-600', bg: 'bg-gray-100', path: PATHS.SETTINGS },
  ];

  return (
    <Page className="bg-surface flex flex-col min-h-screen">
      <Header variant="back" title="Tất cả tính năng" />

      <div className="p-4 flex flex-col gap-5 pb-24">
        {/* Nhóm Thành viên */}
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-3">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
            Nghiệp vụ Thành viên & Sinh viên
          </span>
          <div className="grid grid-cols-4 gap-y-4 gap-x-2">
            {memberShortcuts.map((item) => (
              <div
                key={item.id}
                onClick={() => navigateForward(navigate, item.path)}
                className="flex flex-col items-center gap-1.5 cursor-pointer active:opacity-75"
              >
                <div className={`w-12 h-12 rounded-2xl ${item.bg} ${item.color} flex items-center justify-center`}>
                  <Icon icon={item.icon as any} size={24} />
                </div>
                <span className="text-xs text-gray-700 text-center font-medium line-clamp-1">
                  {item.title}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Nhóm Quản trị */}
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex flex-col gap-3">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
            Quản trị & Hệ thống
          </span>
          <div className="grid grid-cols-4 gap-y-4 gap-x-2">
            {adminShortcuts.map((item) => (
              <div
                key={item.id}
                onClick={() => navigateForward(navigate, item.path)}
                className="flex flex-col items-center gap-1.5 cursor-pointer active:opacity-75"
              >
                <div className={`w-12 h-12 rounded-2xl ${item.bg} ${item.color} flex items-center justify-center`}>
                  <Icon icon={item.icon as any} size={24} />
                </div>
                <span className="text-xs text-gray-700 text-center font-medium line-clamp-1">
                  {item.title}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Page>
  );
};

export default ShortcutsPage;
