import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';

export const useMeetingEvents = (meetingId?: number, enabled: boolean = true) => {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;

    // URL của endpoint SSE
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const sseUrl = `${baseUrl}/meetings/events/stream`;

    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('🔔 Received SSE event:', data);

        // Chỉ xử lý nếu event thuộc về meeting hiện tại (nếu có truyền meetingId)
        if (meetingId && data.meeting_id !== meetingId) return;

        // Tự động invalidate các query liên quan để React Query fetch lại dữ liệu mới
        if (data.type === 'CHECK_IN' || data.type === 'CHECK_OUT') {
          // Refresh danh sách người tham gia
          queryClient.invalidateQueries({ queryKey: ['meetings'] });
          queryClient.invalidateQueries({ queryKey: ['meeting', data.meeting_id] });
          queryClient.invalidateQueries({ queryKey: ['capacity'] });
          queryClient.invalidateQueries({ queryKey: ['activities'] });

          // Hiển thị thông báo nhỏ
          const action = data.type === 'CHECK_IN' ? 'vừa check-in' : 'vừa check-out';
          message.info(`Thành viên ${action} tại buổi họp: ${data.meeting_title}`);
        }
      } catch (error) {
        console.error('❌ Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('❌ SSE Connection Error:', error);
      // Trình duyệt sẽ tự động thử kết nối lại sau vài giây
    };

    // Cleanup khi component unmount hoặc khi bị disabled
    return () => {
      eventSource.close();
    };
  }, [queryClient, meetingId, enabled]);
};
