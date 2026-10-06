import React from 'react';
import { Modal, Button, Typography, Spin } from 'antd';
import { HistoryOutlined } from '@ant-design/icons';
import { useHomeworkSubmissions, useHomework } from '@/features/homework/hooks/useHomeworks';
import type { UserSubmissionInfo } from '@/features/homework/types/homework.types';
import { UnifiedSubmissionTimeline } from './UnifiedSubmissionTimeline';

const { Text } = Typography;

export interface SubmissionHistoryModalProps {
  homeworkId: number | null;
  user: UserSubmissionInfo | null;
  open: boolean;
  onClose: () => void;
}

export const SubmissionHistoryModal: React.FC<SubmissionHistoryModalProps> = ({
  homeworkId,
  user,
  open,
  onClose,
}) => {
  const { data: homework } = useHomework(open && homeworkId ? homeworkId : null);
  const { data: submissions = [], isLoading } = useHomeworkSubmissions(
    open && homeworkId ? homeworkId : null,
    open && user ? user.user_id : null
  );

  return (
    <Modal
      title={
        <div className="flex items-center gap-2.5 pb-1">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <HistoryOutlined className="text-base" />
          </div>
          <div>
            <div className="font-semibold text-base leading-snug text-gray-900 dark:text-gray-100">
              Lịch sử nộp bài chi tiết
            </div>
            <Text type="secondary" className="text-xs font-normal">
              Học viên: <span className="font-medium text-gray-800 dark:text-gray-200">{user?.name || `Học viên #${user?.user_id}`}</span> (ID: #{user?.user_id})
            </Text>
          </div>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose} className="rounded-lg font-medium">
          Đóng
        </Button>,
      ]}
      width={600}
      centered
    >
      <div className="py-2 max-h-[65vh] overflow-y-auto pr-1">
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
          />
        )}
      </div>
    </Modal>
  );
};
