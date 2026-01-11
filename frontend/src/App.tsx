import { AuthProvider, useAuth } from '@/context/AuthContext';
import DashboardPage from '@/pages/DashboardPage';
import LoginPage from '@/pages/LoginPage';
import { ConfigProvider, Spin } from 'antd';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

const AppContent = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-50">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onLoginSuccess={() => { }} />
        }
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
  );
};

function App() {
  return (
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
          <AppContent />
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
