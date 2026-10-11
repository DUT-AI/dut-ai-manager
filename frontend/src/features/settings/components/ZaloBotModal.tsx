import React from 'react';
import { Modal, Typography, Avatar } from 'antd';

const { Text } = Typography;

interface ZaloBotModalProps {
    open: boolean;
    bindCode: string;
    onClose: () => void;
}

export const ZaloBotModal: React.FC<ZaloBotModalProps> = ({ open, bindCode, onClose }) => {
    return (
        <Modal
            title={(
                <>
                    <Avatar
                        src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Icon_of_Zalo.svg/120px-Icon_of_Zalo.svg.png"
                        size="small"
                        className="mr-2"
                    />
                    Liên kết Zalo Bot (Miễn phí)
                </>
            )}
            open={open}
            onCancel={onClose}
            footer={null}
        >
            <div className="flex flex-col items-center p-4">
                <Text className="mb-4 text-center">
                    Để nhận thông báo qua Zalo (miễn phí), vui lòng thực hiện các bước sau:
                </Text>
                <div className="w-full bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
                    <Text strong className="block mb-2">Bước 1:</Text>
                    <Text>Mở ứng dụng Zalo trên điện thoại, tìm kiếm <b>DUT AI Bot</b> (hoặc tên Bot bạn đã tạo).</Text>
                </div>
                <div className="w-full bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
                    <Text strong className="block mb-2">Bước 2:</Text>
                    <Text className="block mb-2">Gửi tin nhắn chính xác bằng đoạn mã sau cho Bot:</Text>
                    <div className="bg-white border-2 border-dashed border-[#0068ff] rounded-lg p-4 text-center">
                        <Text className="text-3xl font-bold tracking-[0.2em] text-[#0068ff]">
                            {bindCode}
                        </Text>
                    </div>
                </div>
                <Text type="secondary" className="text-center italic mt-2">
                    Vui lòng làm mới trang (F5) sau khi bot báo liên kết thành công để cập nhật trạng thái.
                </Text>
            </div>
        </Modal>
    );
};

export default ZaloBotModal;
