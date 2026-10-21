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
        </div>

        {/* Member Menu */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
            <Text className="font-bold text-xs text-gray-500 uppercase tracking-wider">Cá nhân</Text>
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

        {/* Logout / Login Button */}
        <button
          onClick={handleAuthAction}
          className={`w-full py-3.5 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 border transition-all active:scale-[0.98] ${
            isAuthenticated
              ? 'bg-rose-50 text-rose-600 border-rose-100 active:bg-rose-100'
              : 'bg-blue-600 text-white border-blue-600 active:bg-blue-700'
          }`}
        >
          <Icon icon={isAuthenticated ? 'zi-leave' : 'zi-user'} size={18} />
          <span>{isAuthenticated ? 'Đăng xuất tài khoản' : 'Đăng nhập'}</span>
        </button>

        <div className="text-center text-xs text-gray-400 mt-1">
          DUT AI Manager • Zalo Mini App Edition v1.0
        </div>
      </div>
    </Page>
  );
};

export default ProfilePage;
