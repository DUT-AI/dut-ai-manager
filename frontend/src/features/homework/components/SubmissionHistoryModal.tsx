import React, { useState } from 'react';
import { Modal, Button, Typography, Spin, Tooltip } from 'antd';
import {
  HistoryOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons';
import { useHomeworkSubmissions, useHomework } from '@/features/homework/hooks/useHomeworks';
import type { UserSubmissionInfo, ExerciseSummary } from '@/features/homework/types/homework.types';
import { UnifiedSubmissionTimeline } from './UnifiedSubmissionTimeline';

const { Text } = Typography;

export interface SubmissionHistoryModalProps {
  homeworkId: number | null;
  user: UserSubmissionInfo | null;
  open: boolean;
  onClose: () => void;
  allExercises?: ExerciseSummary[] | null;
}

export const SubmissionHistoryModal: React.FC<SubmissionHistoryModalProps> = ({
  homeworkId,
  user,
  open,
  onClose,
  allExercises,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(true);
  const { data: homework } = useHomework(open && homeworkId ? homeworkId : null);
  const { data: submissions = [], isLoading } = useHomeworkSubmissions(
    open && homeworkId ? homeworkId : null,
    open && user ? user.user_id : null
  );

  const hasCodingReq = (user?.total_coding_required ?? 0) > 0;

  return (
    <Modal
      title={
        <div className="flex items-center justify-between gap-2.5 pb-1 pr-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400 flex-shrink-0">
              <HistoryOutlined className="text-base" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-base leading-snug text-gray-900 dark:text-gray-100">
                  Lịch sử nộp bài chi tiết
                </span>
                {hasCodingReq && (
                  <span className={`text-xs px-2 py-0.5 rounded-md font-semibold ${
                    user?.total_coding_completed === user?.total_coding_required
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300'
                      : (user?.total_coding_completed ?? 0) > 0
                        ? 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300'
                        : 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300'
                  }`}>
                    {user?.total_coding_completed ?? 0}/{user?.total_coding_required} bài con
                  </span>
                )}
              </div>
              <Text type="secondary" className="text-xs font-normal">
                Học viên: <span className="font-medium text-gray-800 dark:text-gray-200">{user?.name || `Học viên #${user?.user_id}`}</span> (ID: #{user?.user_id})
              </Text>
            </div>
          </div>
          <Tooltip title={isFullscreen ? 'Thu nhỏ cửa sổ' : 'Phóng to toàn màn hình'}>
            <Button
              type="text"
              size="small"
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
            />
          </Tooltip>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose} className="rounded-lg font-medium">
          Đóng
        </Button>,
      ]}
      width={isFullscreen ? '96vw' : 850}
      style={
        isFullscreen
          ? { top: 16, maxWidth: '1600px', paddingBottom: 0 }
          : { top: 32 }
      }
      styles={{
        body: {
          maxHeight: isFullscreen ? 'calc(100vh - 160px)' : '70vh',
          overflowY: 'auto',
          paddingRight: '12px',
        },
      }}
      centered={!isFullscreen}
      destroyOnClose
    >
      <div className="py-2">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-gray-400">
            <Spin />
            <span className="text-xs">Đang tải dữ liệu bài nộp...</span>
          </div>
        ) : (
          <UnifiedSubmissionTimeline
            submissions={submissions}
            type="CODING"
            deadline={homework?.deadline}
            showExerciseOverview={true}
            allExercises={allExercises}
          />
        )}
      </div>
    </Modal>
  );
};

