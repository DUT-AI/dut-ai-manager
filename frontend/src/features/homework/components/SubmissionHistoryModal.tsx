import React, { useState, useMemo } from 'react';
import { Modal, Button, Typography, Spin, Tooltip, Tabs, Tag } from 'antd';
import {
  HistoryOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  CodeOutlined,
  TrophyOutlined,
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

  const requiresCoding = homework?.requires_coding ?? true;
  const requiresGame = homework?.requires_game ?? false;
  const hasBoth = requiresCoding && requiresGame;

  // Tách biệt dứt khoát bài nộp Coding và Game
  const codingSubmissions = useMemo(
    () => (submissions || []).filter((s) => s.submission_type === 'CODING'),
    [submissions]
  );
  const gameSubmissions = useMemo(
    () => (submissions || []).filter((s) => s.submission_type === 'GAME'),
    [submissions]
  );

  const isGamePassed = useMemo(
    () => gameSubmissions.some((s) => s.is_passed),
    [gameSubmissions]
  );

  const totalCodingRequired = allExercises && allExercises.length > 0
    ? allExercises.length
    : (user?.total_coding_required ?? 0);

  const completedCodingCount = useMemo(() => {
    if (!allExercises || allExercises.length === 0) {
      return user?.total_coding_completed ?? 0;
    }
    const passedExIds = new Set(
      codingSubmissions.filter((s) => s.is_passed).map((s) => s.exercise_id)
    );
    return allExercises.filter((ex) => passedExIds.has(ex.exercise_id || ex.id)).length;
  }, [allExercises, codingSubmissions, user?.total_coding_completed]);

  const hasCodingReq = totalCodingRequired > 0;

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
                  <span
                    className={`text-xs px-2 py-0.5 rounded-md font-semibold ${
                      completedCodingCount === totalCodingRequired
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : completedCodingCount > 0
                          ? 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300'
                          : 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300'
                    }`}
                  >
                    {completedCodingCount}/{totalCodingRequired} bài con
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
        ) : hasBoth ? (
          <Tabs
            defaultActiveKey="coding"
            items={[
              {
                key: 'coding',
                label: (
                  <span className="flex items-center gap-2 font-semibold text-sm">
                    <CodeOutlined className="text-indigo-600" />
                    Bài tập Coding
                    <Tag color={codingSubmissions.length > 0 ? 'success' : 'default'} className="m-0 text-xs rounded-md">
                      {codingSubmissions.length > 0 ? `${codingSubmissions.length} lần nộp` : 'Chưa nộp'}
                    </Tag>
                  </span>
                ),
                children: (
                  <div className="pt-2">
                    <UnifiedSubmissionTimeline
                      submissions={codingSubmissions}
                      type="CODING"
                      deadline={homework?.deadline}
                      showExerciseOverview={true}
                      allExercises={allExercises}
                    />
                  </div>
                ),
              },
              {
                key: 'game',
                label: (
                  <span className="flex items-center gap-2 font-semibold text-sm">
                    <TrophyOutlined className="text-purple-600" />
                    Trắc nghiệm Game
                    <Tag color={isGamePassed ? 'success' : 'default'} className="m-0 text-xs rounded-md">
                      {isGamePassed ? 'Đã hoàn thành' : 'Chưa hoàn thành'}
                    </Tag>
                  </span>
                ),
                children: (
                  <div className="pt-2">
                    <UnifiedSubmissionTimeline
                      submissions={gameSubmissions}
                      type="GAME"
                      deadline={homework?.deadline}
                      showExerciseOverview={false}
                    />
                  </div>
                ),
              },
            ]}
          />
        ) : requiresGame && !requiresCoding ? (
          <UnifiedSubmissionTimeline
            submissions={gameSubmissions}
            type="GAME"
            deadline={homework?.deadline}
            showExerciseOverview={false}
          />
        ) : (
          <UnifiedSubmissionTimeline
            submissions={codingSubmissions}
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
