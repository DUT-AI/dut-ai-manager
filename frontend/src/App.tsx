import { AuthProvider, useAuth, LoginPage, ZaloCallback } from '@/features/auth';
import { CapacityProvider } from '@/context/CapacityContext';
import DashboardPage from '@/pages/DashboardPage';
import { queryClient } from '@/lib/queryClient';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ConfigProvider, Spin, notification } from 'antd';
import { AnimatePresence } from 'motion/react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';

import { useEffect } from 'react';
import { PwaInstallPrompt, PushBanner } from '@/features/pwa/components';

const AppContent = () => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('PWA ServiceWorker registered with scope: ', registration.scope);
        })
        .catch((err) => {
          console.warn('PWA ServiceWorker registration failed: ', err);
        });

      // Lắng nghe sự kiện push do Service Worker broadcast tới tab
      const handleSwMessage = (event: MessageEvent) => {
        if (event.data?.type === 'PUSH_NOTIFICATION_RECEIVED') {
          const pushData = event.data.data;
          console.log('🔔 [DUT AI Manager] Nhận Push Event từ Service Worker:', pushData);
          notification.info({
            message: pushData?.title || 'Thông báo mới từ DUT AI',
            description: pushData?.body || 'Bạn có thông báo mới từ hệ thống.',
            placement: 'topRight',
            duration: 6,
          });
        }
      };

      navigator.serviceWorker.addEventListener('message', handleSwMessage);
      return () => {
        navigator.serviceWorker.removeEventListener('message', handleSwMessage);
      };
    }
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-50">
        <Spin size="large" />
      </div>
    );
  }

  const routeKey = location.pathname.startsWith('/dashboard') ? 'dashboard-shell' : location.pathname;

  return (
    <div className="min-h-screen flex flex-col">
      {isAuthenticated && <PushBanner />}
      <PwaInstallPrompt />
      <div className="flex-1">
        <AnimatePresence mode="wait">
          <Routes location={location} key={routeKey}>
            <Route
              path="/login"
              element={
                isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onLoginSuccess={() => { }} />
              }
            />
            <Route
              path="/auth/zalo/callback"
              element={<ZaloCallback />}
            />
            <Route
              path="/dashboard/*"
              element={
                isAuthenticated ? <DashboardPage /> : <Navigate to="/login" replace />
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AnimatePresence>
      </div>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#4f46e5',
            borderRadius: 12,
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
          },
        }}
      >
        <BrowserRouter>
          <AuthProvider>
            <CapacityProvider>
              <AppContent />
            </CapacityProvider>
          </AuthProvider>
        </BrowserRouter>
      </ConfigProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}


export default App;
