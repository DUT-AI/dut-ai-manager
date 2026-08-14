import React from 'react';
import { Page, Box, Text, Button, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { navigateForward } from '@/utils/navigation';
import { PATHS } from '@/constants/paths';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, isAdminOrLeader } = useAuth();

  const handleAuthAction = () => {
    if (isAuthenticated) {
      logout();
    } else {
      navigateForward(navigate, PATHS.LOGIN);
    }
  };

  return (
    <Page className="bg-surface flex flex-col min-h-screen">
      <Header title="Tài khoản & Quản trị" showBack={false} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-4 pb-24">
        {/* User Card */}
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-lg overflow-hidden border border-blue-200">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
              ) : (
                <span>{user?.name ? user.name.charAt(0).toUpperCase() : 'U'}</span>
              )}
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-gray-900 text-base">
                {user?.name || (isAuthenticated ? 'Người dùng DUT' : 'Khách vãng lai')}
              </span>
              <span className="text-xs text-gray-500">{user?.email || 'Chưa đăng nhập hệ thống'}</span>
              {isAuthenticated && (
                <div className="flex items-center gap-1.5 mt-1.5">
                  {(user?.role_names || ['member']).map((role) => (
                    <span
                      key={role}
                      className="bg-blue-50 text-blue-700 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <Button
            size="small"
            variant={isAuthenticated ? 'secondary' : 'primary'}
            className="rounded-xl text-xs"
            onClick={handleAuthAction}
          >
            {isAuthenticated ? 'Đăng xuất' : 'Đăng nhập'}
          </Button>
        </div>

        {/* Member Menu */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
            <Text className="font-bold text-xs text-gray-500 uppercase tracking-wider">Cá nhân</Text>
          </div>

          <div
            onClick={() => navigateForward(navigate, PATHS.INVOICES)}
            className="flex items-center justify-between p-4 border-b border-gray-100 cursor-pointer active:bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <Icon icon="zi-wallet" className="text-blue-600" size={20} />
              <span className="text-sm font-medium text-gray-800">Hóa đơn của tôi</span>
            </div>
            <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
          </div>

          <div
            onClick={() => navigateForward(navigate, PATHS.SETTINGS)}
            className="flex items-center justify-between p-4 cursor-pointer active:bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <Icon icon="zi-setting" className="text-gray-600" size={20} />
              <span className="text-sm font-medium text-gray-800">Cài đặt tài khoản & Thẻ</span>
            </div>
            <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
          </div>
        </div>

        {/* Management Menu (Admin/Leader only) */}
        {isAdminOrLeader() && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
            <div className="px-4 py-3 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
              <Text className="font-bold text-xs text-indigo-700 uppercase tracking-wider">
                Khu vực Quản trị (Leader / Admin)
              </Text>
              <span className="bg-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                Admin
              </span>
            </div>

            <div
              onClick={() => navigateForward(navigate, PATHS.USERS)}
              className="flex items-center justify-between p-4 border-b border-gray-100 cursor-pointer active:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <Icon icon="zi-user" className="text-indigo-600" size={20} />
                <span className="text-sm font-medium text-gray-800">Quản lý Thành viên</span>
              </div>
              <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
            </div>

            <div
              onClick={() => navigateForward(navigate, PATHS.TEAMS)}
              className="flex items-center justify-between p-4 border-b border-gray-100 cursor-pointer active:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <Icon icon="zi-members" className="text-indigo-600" size={20} />
                <span className="text-sm font-medium text-gray-800">Quản lý Nhóm (Teams)</span>
              </div>
              <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
            </div>

            <div
              onClick={() => navigateForward(navigate, PATHS.RBAC)}
              className="flex items-center justify-between p-4 border-b border-gray-100 cursor-pointer active:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <Icon icon="zi-shield-check" className="text-indigo-600" size={20} />
                <span className="text-sm font-medium text-gray-800">Phân quyền RBAC</span>
              </div>
              <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
            </div>

            <div
              onClick={() => navigateForward(navigate, PATHS.ADMIN_BILLING)}
              className="flex items-center justify-between p-4 cursor-pointer active:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <Icon icon="zi-check-circle" className="text-indigo-600" size={20} />
                <span className="text-sm font-medium text-gray-800">Quản lý Thu chi & Quỹ</span>
              </div>
              <Icon icon="zi-chevron-right" size={18} className="text-gray-400" />
            </div>
          </div>
        )}

        <div className="text-center text-xs text-gray-400 mt-2">
          DUT AI Manager • Zalo Mini App Edition v1.0
        </div>
      </div>
    </Page>
  );
};

export default ProfilePage;
