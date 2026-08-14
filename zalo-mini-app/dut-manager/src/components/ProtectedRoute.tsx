import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { PATHS } from '@/constants/paths';
import { Box, Spinner, Text } from 'zmp-ui';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Guard Component bảo vệ các trang yêu cầu đăng nhập.
 * Nếu chưa đăng nhập, tự động chuyển hướng về trang Login.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Điều hướng về trang login nếu chưa đăng nhập
      navigate(PATHS.LOGIN, {
        replace: true,
        state: { from: location.pathname },
      });
    }
  }, [isAuthenticated, loading, navigate, location]);

  // Trong lúc đang kiểm tra phiên đăng nhập từ cache/storage
  if (loading) {
    return (
      <Box className="flex flex-col items-center justify-center min-h-screen bg-surface gap-3">
        <Spinner visible logo="" />
        <Text className="text-xs text-gray-500">Đang kiểm tra thông tin đăng nhập...</Text>
      </Box>
    );
  }

  // Nếu chưa xác thực, không render nội dung trang được bảo vệ
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
