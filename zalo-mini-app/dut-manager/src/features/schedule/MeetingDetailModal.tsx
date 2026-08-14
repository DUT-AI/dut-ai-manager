import React, { useRef, useState } from 'react';
import { Modal, Button, Icon, useSnackbar } from 'zmp-ui';
import type { MeetingResponse, ParticipantResponse } from '@/types/meeting.types';
import { ParticipantStatus } from '@/types/meeting.types';
import { meetingService } from '@/services/api/meeting.service';
import { formatTime, formatDateFull } from './MeetingCard';

interface MeetingDetailModalProps {
  meeting: MeetingResponse | null;
  currentUserId?: number;
  hasUpdatePermission: boolean;
  hasDeletePermission: boolean;
  onClose: () => void;
  onOpenEdit: (meeting: MeetingResponse) => void;
  onDelete: (id: number) => void;
  onRefetch: () => void;
}

export const MeetingDetailModal: React.FC<MeetingDetailModalProps> = ({
  meeting,
  currentUserId,
  hasUpdatePermission,
  hasDeletePermission,
  onClose,
  onOpenEdit,
  onDelete,
  onRefetch,
}) => {
  const { openSnackbar } = useSnackbar();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isCheckingIn, setIsCheckingIn] = useState<boolean>(false);

  if (!meeting) return null;

  const now = new Date();
  const start = new Date(meeting.start_time);
  const end = new Date(meeting.end_time);
  const isOngoing = now >= start && now <= end;
  const isEnded = now > end;

  const myParticipant = meeting.participants?.find((p) => p.user_id === currentUserId);
  const myCheckedIn =
    myParticipant?.status === ParticipantStatus.JOINED ||
    myParticipant?.status === ParticipantStatus.COMPLETED;

  const total = meeting.participants?.length || 0;
  const checkedIn =
    meeting.participants?.filter(
      (p) => p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED
    ).length || 0;

  const handleTriggerCheckIn = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentUserId) return;

    setIsCheckingIn(true);
    try {
      const res = await meetingService.checkIn(meeting.id, currentUserId, file);
      if (res.is_success) {
        openSnackbar({ text: 'Điểm danh thành công!', type: 'success' });
        onRefetch();
      } else {
        openSnackbar({ text: res.message || 'Điểm danh thất bại', type: 'error' });
      }
    } catch (err: any) {
      openSnackbar({ text: err?.message || 'Lỗi khi gửi ảnh điểm danh', type: 'error' });
    } finally {
      setIsCheckingIn(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <Modal
      visible={meeting !== null}
      title="Chi tiết Cuộc họp"
      onClose={onClose}
      maskClosable
    >
      <div className="flex flex-col gap-4 py-2">
        {/* Title & Status */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${
                isOngoing
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : isEnded
                  ? 'bg-gray-100 text-gray-500 border-gray-200'
                  : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}
            >
              {isOngoing ? '🟢 Đang diễn ra' : isEnded ? '⚫ Đã kết thúc' : '🔵 Sắp diễn ra'}
            </span>
            {meeting.require_check_in && (
              <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full font-semibold">
                Bắt buộc checkin
              </span>
            )}
          </div>
          <h3 className="font-bold text-gray-900 text-base">{meeting.title}</h3>
        </div>

        {/* Time Info */}
        <div className="bg-gray-50 p-3 rounded-xl border border-gray-100 flex flex-col gap-1.5 text-xs text-gray-600">
          <div className="flex items-center gap-2 font-medium">
            <Icon icon="zi-calendar" size={15} />
            <span>{formatDateFull(meeting.start_time)}</span>
          </div>
          <div className="flex items-center gap-2 font-bold text-blue-700">
            <Icon icon="zi-clock-1" size={15} />
            <span>
              {formatTime(meeting.start_time)} - {formatTime(meeting.end_time)}
            </span>
          </div>
        </div>

        {/* Content */}
        {meeting.content && (
          <div className="flex flex-col gap-1 text-xs">
            <span className="text-gray-400">Nội dung cuộc họp:</span>
            <p className="text-xs text-gray-700 bg-gray-50 p-3 rounded-xl border border-gray-100 leading-relaxed font-normal whitespace-pre-wrap">
              {meeting.content}
            </p>
          </div>
        )}

        {/* Check-in Banner / Button */}
        {meeting.require_check_in && currentUserId && (
          <div className="bg-blue-50/70 border border-blue-200 p-3 rounded-xl flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-bold text-xs text-blue-900">Điểm danh chụp ảnh</span>
              <span className="text-[11px] text-blue-700">
                {myCheckedIn ? '✓ Bạn đã hoàn tất điểm danh' : 'Chụp ảnh có mặt để check-in'}
              </span>
            </div>

            <input
              type="file"
              accept="image/*"
              capture="user"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />

            {!myCheckedIn ? (
              <Button
                size="small"
                loading={isCheckingIn}
                className="rounded-xl font-bold text-xs bg-blue-600 text-white"
                onClick={handleTriggerCheckIn}
              >
                Chụp ảnh Check-in
              </Button>
            ) : (
              <span className="text-xs font-bold text-emerald-600 bg-emerald-100/70 px-2.5 py-1 rounded-lg">
                Đã checkin
              </span>
            )}
          </div>
        )}

        {/* Participants Summary & List */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-gray-800">
              Danh sách tham gia ({checkedIn}/{total} đã điểm danh)
            </span>
          </div>

          <div className="max-h-48 overflow-y-auto flex flex-col gap-1.5 pr-1">
            {meeting.participants?.length === 0 ? (
              <span className="text-xs text-gray-400 italic">Chưa có thành viên nào được chỉ định</span>
            ) : (
              meeting.participants.map((p) => {
                const isUserCheckedIn =
                  p.status === ParticipantStatus.JOINED || p.status === ParticipantStatus.COMPLETED;

                return (
                  <div
                    key={p.id || p.user_id}
                    className="flex items-center justify-between p-2 rounded-xl bg-gray-50 border border-gray-100 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-[10px]">
                        {p.user_name ? p.user_name.charAt(0) : 'U'}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-semibold text-gray-800">
                          {p.user_name || `Thành viên #${p.user_id}`}
                        </span>
                        {p.check_in_at && (
                          <span className="text-[10px] text-gray-400">
                            Checkin lúc: {formatTime(p.check_in_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        isUserCheckedIn
                          ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {isUserCheckedIn ? 'Đã check-in' : 'Chưa tham gia'}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2 border-t border-gray-100">
          <Button type="neutral" className="flex-1 rounded-xl" onClick={onClose}>
            Đóng
          </Button>
          {hasUpdatePermission && (
            <Button
              className="flex-1 rounded-xl font-bold bg-blue-600 text-white"
              onClick={() => {
                const target = meeting;
                onClose();
                onOpenEdit(target);
              }}
            >
              Chỉnh sửa
            </Button>
          )}
          {hasDeletePermission && (
            <Button
              type="danger"
              className="rounded-xl font-bold"
              onClick={() => {
                const targetId = meeting.id;
                onClose();
                onDelete(targetId);
              }}
            >
              Xóa
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};
