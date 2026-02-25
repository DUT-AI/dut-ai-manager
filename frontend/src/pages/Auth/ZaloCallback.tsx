import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Spin, Result, Button, message } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { zaloService } from '@/services/api/zalo.service';

const ZaloCallback = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [errorMsg, setErrorMsg] = useState('');
    const hasFetched = React.useRef(false);

    useEffect(() => {
        const handleCallback = async () => {
            if (hasFetched.current) return;
            hasFetched.current = true;
            try {
                // Get code from URL
                const searchParams = new URLSearchParams(location.search);
                const code = searchParams.get('code');

                if (!code) {
                    throw new Error('Không tìm thấy mã xác thực từ Zalo');
                }

                // Get code_verifier from localStorage
                const verifier = localStorage.getItem('zalo_code_verifier');
                if (!verifier) {
                    throw new Error('Phiên đăng nhập không hợp lệ hoặc đã hết hạn');
                }

                // Call API to bind
                await zaloService.bindZaloAccount(code, verifier);

                // Cleanup
                localStorage.removeItem('zalo_code_verifier');

                setStatus('success');
                message.success('Liên kết tài khoản Zalo thành công!');

                // Redirect back to profile after 2s
                setTimeout(() => {
                    navigate('/dashboard/profile', { replace: true });
                }, 2000);

            } catch (err: any) {
                setStatus('error');
                setErrorMsg(err.message || 'Có lỗi xảy ra khi xác thực với Zalo');
            }
        };

        handleCallback();
    }, [location, navigate]);

    return (
        <div className="flex h-screen w-full items-center justify-center bg-gray-50">
            <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-sm border border-gray-100 text-center">
                {status === 'loading' && (
                    <div className="flex flex-col items-center justify-center py-8">
                        <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
                        <h2 className="mt-6 text-xl font-semibold text-gray-800">Đang xử lý...</h2>
                        <p className="mt-2 text-gray-500">Vui lòng đợi trong giây lát, đang liên kết tài khoản định danh Zalo của bạn.</p>
                    </div>
                )}

                {status === 'success' && (
                    <Result
                        status="success"
                        title="Liên kết thành công!"
                        subTitle="Tài khoản Zalo của bạn đã được liên kết với hệ thống. Trình duyệt sẽ tự động chuyển hướng..."
                    />
                )}

                {status === 'error' && (
                    <Result
                        status="error"
                        title="Liên kết thất bại"
                        subTitle={errorMsg}
                        extra={[
                            <Button type="primary" key="back" onClick={() => navigate('/dashboard/profile')}>
                                Quay lại trang cá nhân
                            </Button>
                        ]}
                    />
                )}
            </div>
        </div>
    );
};

export default ZaloCallback;
