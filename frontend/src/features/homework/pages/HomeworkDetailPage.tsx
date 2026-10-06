import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Tabs,
  Tag,
  Button,
  Space,
  Spin,
  Empty,
  Card,
  message,
  Breadcrumb,
} from 'antd';
import {
  ArrowLeftOutlined,
  SyncOutlined,
  CodeOutlined,
  PlayCircleOutlined,
  ExportOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  WarningOutlined,
  FileDoneOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import {
  useHomework,
  useHomeworkSubmissionStatus,
  useSyncHomeworkFromQuiz,
} from '../hooks/useHomeworks';
import type { UserSubmissionInfo } from '../types/homework.types';
import { HomeworkOverviewStats } from '../components/HomeworkOverviewStats';
import { UserSubmissionCategoryView } from '../components/UserSubmissionCategoryView';
import { SubmissionHistoryModal } from '../components/SubmissionHistoryModal';
import { DeadlineText } from '../components/DeadlineText';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Title, Text } = Typography;

export const HomeworkDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const homeworkId = id ? Number(id) : null;

  const { data: homework, isLoading: isHwLoading } = useHomework(homeworkId);
  const {
    data: statusData,
    isLoading: isStatusLoading,
    refetch,
  } = useHomeworkSubmissionStatus(homeworkId);
  const syncMutation = useSyncHomeworkFromQuiz();

  const [historyUser, setHistoryUser] = useState<UserSubmissionInfo | null>(null);

  const isLoading = isHwLoading || isStatusLoading;
  const isOverdue = homework ? dayjs().isAfter(dayjs(homework.deadline)) : false;

  const handleSync = async () => {
    if (!homeworkId) return;
    try {
      const res = await syncMutation.mutateAsync(homeworkId);
      message.success(res?.message || 'Đồng bộ từ Quiz thành công!');
      refetch();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Đồng bộ từ Quiz thất bại');
    }
  };

  const handleViewHistory = (user: UserSubmissionInfo) => {
    setHistoryUser(user);
  };

  // Chuẩn bị dữ liệu Coding & Game
  const codingStatus = useMemo(() => {
    return (
      statusData?.coding ?? {
        submitted: statusData?.submitted ?? [],
        not_submitted: statusData?.not_submitted ?? [],
      }
    );
  }, [statusData]);

  const gameStatus = useMemo(() => {
    return statusData?.game ?? { submitted: [], not_submitted: [] };
  }, [statusData]);

  const hasCoding = homework?.requires_coding ?? true;
  const hasGame = homework?.requires_game ?? false;

  const codingSubmittedCount = codingStatus.submitted.length;
  const codingTotalCount = codingSubmittedCount + codingStatus.not_submitted.length;

  const gameSubmittedCount = gameStatus.submitted.length;
  const gameTotalCount = gameSubmittedCount + gameStatus.not_submitted.length;

  const totalSubmitted =
    statusData?.submitted?.length ??
    (hasCoding && !hasGame
      ? codingSubmittedCount
      : !hasCoding && hasGame
        ? gameSubmittedCount
        : Math.max(codingSubmittedCount, gameSubmittedCount));

  const totalAssigned =
    (statusData?.submitted?.length ?? 0) + (statusData?.not_submitted?.length ?? 0) ||
    (hasCoding && !hasGame
      ? codingTotalCount
      : !hasCoding && hasGame
        ? gameTotalCount
        : Math.max(codingTotalCount, gameTotalCount));

  const submissionPercent =
    totalAssigned > 0 ? Math.round((totalSubmitted / totalAssigned) * 100) : 0;

  // Tabs for Submissions
  const tabItems = useMemo(() => {
    const items = [];

    if (hasCoding) {
      items.push({
        key: 'coding',
        label: (
          <span className="flex items-center gap-2 font-semibold text-sm">
            <CodeOutlined className="text-indigo-600" />
            Bài tập Coding
            {codingTotalCount > 0 && (
              <Tag color="indigo" className="m-0 text-xs px-2 py-0.2 rounded-full font-semibold">
                {codingSubmittedCount}/{codingTotalCount}
              </Tag>
            )}
          </span>
        ),
        children: (
          <div className="pt-2">
            <UserSubmissionCategoryView
              status={codingStatus}
              isLoading={isStatusLoading}
              isOverdue={isOverdue}
              onViewHistory={handleViewHistory}
            />
          </div>
        ),
      });
    }

    if (hasGame) {
      items.push({
        key: 'game',
        label: (
          <span className="flex items-center gap-2 font-semibold text-sm">
            <PlayCircleOutlined className="text-purple-600" />
            Quiz Game
            {gameTotalCount > 0 && (
              <Tag color="purple" className="m-0 text-xs px-2 py-0.2 rounded-full font-semibold">
                {gameSubmittedCount}/{gameTotalCount}
              </Tag>
            )}
          </span>
        ),
        children: (
          <div className="pt-2">
            <UserSubmissionCategoryView
              status={gameStatus}
              isLoading={isStatusLoading}
              isOverdue={isOverdue}
              onViewHistory={handleViewHistory}
            />
          </div>
        ),
      });
    }

    if (items.length === 0) {
      items.push({
        key: 'default',
        label: (
          <span className="flex items-center gap-1.5 font-semibold text-sm">
            <CodeOutlined className="text-indigo-600" />
            Danh sách nộp bài
          </span>
        ),
        children: (
          <div className="pt-2">
            <UserSubmissionCategoryView
              status={codingStatus}
              isLoading={isStatusLoading}
              isOverdue={isOverdue}
              onViewHistory={handleViewHistory}
            />
          </div>
        ),
      });
    }

    return items;
  }, [
    hasCoding,
    hasGame,
    codingStatus,
    gameStatus,
    codingSubmittedCount,
    codingTotalCount,
    gameSubmittedCount,
    gameTotalCount,
    isStatusLoading,
    isOverdue,
  ]);

  if (isLoading && !homework) {
    return (
      <div className="p-8 flex flex-col justify-center items-center gap-3 min-h-[60vh]">
        <Spin size="large" />
        <Text type="secondary" className="text-sm">Đang tải thông tin chi tiết bài tập...</Text>
      </div>
    );
  }

  if (!homework) {
    return (
      <div className="p-8">
        <Empty description="Không tìm thấy bài tập yêu cầu">
          <Button type="primary" onClick={() => navigate('/dashboard/homeworks')}>
            Quay lại danh sách bài tập
          </Button>
        </Empty>
      </div>
    );
  }

  const deadlineObj = dayjs(homework.deadline);

  return (
    <div className="p-4 sm:p-6 lg:p-8 w-full space-y-6">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Breadcrumb
          items={[
            {
              title: (
                <span
                  onClick={() => navigate('/dashboard/homeworks')}
                  className="cursor-pointer text-gray-500 hover:text-indigo-600 transition-colors"
                >
                  Quản lý Bài tập
                </span>
              ),
            },
            {
              title: <span className="font-semibold text-gray-800 dark:text-gray-200 truncate max-w-[280px]">{homework.title}</span>,
            },
          ]}
        />

        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard/homeworks')}
          className="rounded-lg font-medium"
        >
          Quay lại
        </Button>
      </div>

      {/* Main Header Card */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 shadow-xs">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-gray-100 dark:border-zinc-700/80">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-lg">
                <FileDoneOutlined />
              </div>
              <Title level={4} className="!mb-0 !text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                {homework.title}
              </Title>
              {isOverdue ? (
                <Tag color="error" icon={<WarningOutlined />} className="text-xs rounded-md font-semibold">
                  Đã hết hạn
                </Tag>
              ) : (
                <Tag color="success" icon={<ClockCircleOutlined />} className="text-xs rounded-md font-semibold">
                  Đang mở
                </Tag>
              )}
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 flex-wrap pt-1">
              <span className="flex items-center gap-1.5">
                <CalendarOutlined className="text-indigo-500" />
                <b>Hạn nộp:</b> {deadlineObj.format('DD/MM/YYYY HH:mm')} ({deadlineObj.fromNow()})
              </span>
              {homework.slug && (
                <span className="font-mono text-gray-400">
                  Slug: {homework.slug}
                </span>
              )}
            </div>
          </div>

          <Space size="middle" wrap>
            <Button
              icon={<SyncOutlined spin={syncMutation.isPending} className="text-indigo-600" />}
              loading={syncMutation.isPending}
              onClick={handleSync}
              className="rounded-xl font-semibold hover:border-indigo-400 h-9"
            >
              Đồng bộ từ Quiz
            </Button>

            {homework.link && (
              <Button
                type="primary"
                href={homework.link}
                target="_blank"
                rel="noopener noreferrer"
                icon={<ExportOutlined />}
                className="bg-indigo-600 hover:bg-indigo-700 rounded-xl font-semibold h-9"
              >
                Mở link Quiz
              </Button>
            )}
          </Space>
        </div>

        {/* Overview Stats */}
        <div className="pt-4">
          <HomeworkOverviewStats
            hasCoding={hasCoding}
            hasGame={hasGame}
            codingSubmittedCount={codingSubmittedCount}
            codingTotalCount={codingTotalCount}
            gameSubmittedCount={gameSubmittedCount}
            gameTotalCount={gameTotalCount}
            totalSubmitted={totalSubmitted}
            totalAssigned={totalAssigned}
            submissionPercent={submissionPercent}
          />
        </div>
      </div>

      {/* Submissions Tabs Section */}
      <Card className="rounded-2xl border border-gray-100 dark:border-zinc-700 shadow-xs bg-white dark:bg-zinc-800">
        <Tabs
          defaultActiveKey={hasCoding ? 'coding' : 'game'}
          items={tabItems}
          className="homework-detail-tabs"
        />
      </Card>

      {/* Submission History Modal for Individual Student */}
      <SubmissionHistoryModal
        homeworkId={homeworkId}
        user={historyUser}
        open={!!historyUser}
        onClose={() => setHistoryUser(null)}
      />
    </div>
  );
};
export default HomeworkDetailPage;
