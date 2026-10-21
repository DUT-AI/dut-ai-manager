import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App, ZMPRouter, SnackbarProvider, Text, Box, BottomNavigation } from 'zmp-ui';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import HomePage from '@/pages/HomePage';
import CalendarPage from '@/pages/CalendarPage';
import NotificationPage from '@/pages/NotificationPage';
import ProfilePage from '@/pages/ProfilePage';
import LoginPage from '@/pages/LoginPage';
import ShortcutsPage from '@/pages/ShortcutsPage';
import PermissionsPage from '@/pages/PermissionsPage';
import MeetingDetailPage from '@/pages/MeetingDetailPage';
import FeaturePlaceholderPage from '@/pages/FeaturePlaceholderPage';

import ProtectedRoute from '@/components/ProtectedRoute';

import {
  HomeNavIcon,
  CalendarNavIcon,
  NotificationNavIcon,
  UserNavIcon,
} from '@/components/CustomIcons';
import { navigateTab, getNavigationDirection } from '@/utils/navigation';
import Header from '@/components/Header';
import { PATHS, PATH_TO_TAB } from '@/constants/paths';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { notificationService } from '@/services/api/notification.service';
import { useQuery } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AnimatedRoutes: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const direction = getNavigationDirection();
  const activeTab = PATH_TO_TAB[location.pathname] || 'home';
  const isMainTab = !!PATH_TO_TAB[location.pathname];

  const { isAuthenticated } = useAuth();
  const { data: unreadData } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: async () => {
      const res = await notificationService.getUnreadCount();
      return res.data?.unread_count ?? 0;
    },
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });
  const unreadCount = unreadData ?? 0;

  const handleTabChange = (key: string): void => {
    navigateTab(navigate, activeTab, key);
  };

  const isLoginPage = location.pathname === PATHS.LOGIN;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {!isMainTab || isLoginPage ? null : (
        <Header variant="logo" unreadCount={unreadCount} />
      )}

      <TransitionGroup
        className={`page-transition-group flex-1 ${
          direction === 'forward' ? 'slide-forward' : 'slide-backward'
        }`}
      >
        <CSSTransition key={location.pathname} classNames="page" timeout={300}>
          <Routes location={location}>
            {/* 4 Main Tabs (All Protected) */}
            <Route
              path={PATHS.HOME}
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.CALENDAR}
              element={
                <ProtectedRoute>
                  <CalendarPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.NOTIFICATIONS}
              element={
                <ProtectedRoute>
                  <NotificationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.PROFILE}
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />

            {/* Auth */}
            <Route path={PATHS.LOGIN} element={<LoginPage />} />

            {/* Sub-routes / Features (Protected) */}
            <Route
              path={PATHS.SHORTCUTS}
              element={
                <ProtectedRoute>
                  <ShortcutsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.ACADEMIC_REPORTS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Báo cáo Học tập" icon="zi-file" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.ACTIVITY_REPORTS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Báo cáo Hoạt động" icon="zi-check-circle" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.ACTIVITIES}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Lịch Hoạt động" icon="zi-calendar" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.MEETINGS}
              element={
                <ProtectedRoute>
                  <CalendarPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.MEETING_DETAIL}
              element={
                <ProtectedRoute>
                  <MeetingDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.PERMISSIONS}
              element={
                <ProtectedRoute>
                  <PermissionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.VIOLATIONS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Quản lý Vi phạm" icon="zi-warning" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.HOMEWORKS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Bài tập về nhà" icon="zi-list-1" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.INVOICES}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Hóa đơn của tôi" icon="zi-check-circle" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.SETTINGS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Cài đặt hệ thống" icon="zi-setting" />
                </ProtectedRoute>
              }
            />

            {/* Admin / Leader Routes (Protected) */}
            <Route
              path={PATHS.USERS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Quản lý Thành viên" icon="zi-user" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.TEAMS}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Quản lý Nhóm (Teams)" icon="zi-members" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.RBAC}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Quản lý Phân quyền RBAC" icon="zi-shield-solid" />
                </ProtectedRoute>
              }
            />
            <Route
              path={PATHS.ADMIN_BILLING}
              element={
                <ProtectedRoute>
                  <FeaturePlaceholderPage title="Quản lý Thu chi & Quỹ" icon="zi-check-circle" />
                </ProtectedRoute>
              }
            />



            <Route
              path="*"
              element={
                <Box p={4} className="text-center">
                  <Text className="text-gray-500">Trang không tồn tại</Text>
                </Box>
              }
            />
          </Routes>
        </CSSTransition>
      </TransitionGroup>

      {isMainTab && !isLoginPage && (
        <BottomNavigation fixed activeKey={activeTab} onChange={handleTabChange}>
          <BottomNavigation.Item
            key="home"
            label="Trang chủ"
            icon={<HomeNavIcon size={24} />}
            activeIcon={<HomeNavIcon active size={24} />}
          />
          <BottomNavigation.Item
            key="calendar"
            label="Lịch & Họp"
            icon={<CalendarNavIcon size={24} />}
            activeIcon={<CalendarNavIcon active size={24} />}
          />
          <BottomNavigation.Item
            key="notifications"
            label="Thông báo"
            icon={
              <div className="relative flex items-center justify-center">
                <NotificationNavIcon size={24} />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-2 bg-rose-500 text-white text-[9px] font-bold rounded-full min-w-4 h-4 px-1 flex items-center justify-center border-2 border-white">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </div>
            }
            activeIcon={
              <div className="relative flex items-center justify-center">
                <NotificationNavIcon active size={24} />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-2 bg-rose-500 text-white text-[9px] font-bold rounded-full min-w-4 h-4 px-1 flex items-center justify-center border-2 border-white">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </div>
            }
          />
          <BottomNavigation.Item
            key="profile"
            label="Cá nhân"
            icon={<UserNavIcon size={24} />}
            activeIcon={<UserNavIcon active size={24} />}
          />
        </BottomNavigation>
      )}
    </div>
  );
};

import ErrorBoundary from '@/components/ErrorBoundary';

const MyApp: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <App>
        <SnackbarProvider>
          <AuthProvider>
            <ZMPRouter>
              <ErrorBoundary>
                <AnimatedRoutes />
              </ErrorBoundary>
            </ZMPRouter>
          </AuthProvider>
        </SnackbarProvider>
      </App>
    </QueryClientProvider>
  );
};

export default MyApp;
