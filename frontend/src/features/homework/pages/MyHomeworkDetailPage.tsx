import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Tabs,
  Tag,
  Button,
  Spin,
  Empty,
  Card,
  Alert,
  Breadcrumb,
  Space,
  message,
} from 'antd';
import {
  ArrowLeftOutlined,
  CodeOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  ExportOutlined,
  ThunderboltOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  BookOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import {
  useMyHomeworkDetail,
  useSyncHomeworkFromQuiz,
} from '../hooks/useHomeworks';
import {
  MyHomeworkExerciseChecklist,
  UnifiedSubmissionTimeline,
} from '../components';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Title, Text } = Typography;

export const MyHomeworkDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const homeworkId = id ? Number(id) : null;

  const { data: detail, isLoading } = useMyHomeworkDetail(homeworkId);
  const { mutate: syncHomework, isPending: isSyncing } = useSyncHomeworkFromQuiz();

  const homework = detail?.homework;
  const codingExercises = useMemo(() => detail?.coding_exercises ?? [], [detail?.coding_exercises]);
  const submissions = useMemo(() => detail?.submissions ?? [], [detail?.submissions]);

  const codingSubmissions = useMemo(
    () => submissions.filter((s) => s.submission_type === 'CODING'),
    [submissions]
  );
  const gameSubmissions = useMemo(
    () => submissions.filter((s) => s.submission_type === 'GAME'),
    [submissions]
  );

  // Convert official coding exercises into summary items for timeline overview
  const timelineExercises = useMemo(
    () =>
      codingExercises.map((ex) => ({
        exercise_id: ex.exercise_id,
        title: ex.title,
        order_index: ex.order_index ?? 0,
        completed_count: 0,
        total_assigned: 0,
        completion_rate: 0,
      })),
    [codingExercises]
  );

  if (isLoading && !homework) {
    return (
      <div className="p-8 flex flex-col justify-center items-center gap-3 min-h-[60vh]">
        <Spin size="large" />
        <Text type="secondary" className="text-sm">Đang tải chi tiết bài tập...</Text>
      </div>
    );
  }

  if (!homework) {
    return (
      <div className="p-8">
        <Empty description="Không tìm thấy bài tập yêu cầu hoặc bạn chưa được giao bài tập này">
          <Button type="primary" onClick={() => navigate('/dashboard/my-homeworks')}>
            Quay lại Bài tập của tôi
          </Button>
        </Empty>
      </div>
    );
  }

  // Pure presentation from Backend SSOT evaluation
  const completionStatus = homework.completion_status ?? 'NOT_STARTED';
  const timelinessStatus = homework.timeliness_status ?? 'UPCOMING';
  const isCompleted = completionStatus === 'COMPLETED';
  const isCompletedLate = isCompleted && timelinessStatus === 'LATE';
  const isInProgress = completionStatus === 'IN_PROGRESS';
  const isOverdue = timelinessStatus === 'OVERDUE';

  const requiresCoding = homework.has_coding ?? homework.requires_coding ?? true;
  const requiresGame = homework.has_game ?? homework.requires_game ?? false;
  const hasBoth = requiresCoding && requiresGame;
  const hasOnlyCoding = requiresCoding && !requiresGame;
  const hasOnlyGame = !requiresCoding && requiresGame;

  const deadlineObj = homework.deadline ? dayjs(homework.deadline) : null;

  const handleSync = () => {
    if (!homework.id) return;
    syncHomework(homework.id, {
      onSuccess: (res) => {
        message.success(res?.message || 'Đã đồng bộ dữ liệu mới nhất từ Quiz.');
      },
      onError: () => {
        message.error('Không thể đồng bộ từ Quiz. Vui lòng thử lại sau.');
      },
    });
  };

  const renderStatusTag = () => {
    if (isCompleted && !isCompletedLate) {
      return (
        <Tag color="success" icon={<CheckCircleOutlined />} className="text-xs rounded-md font-semibold">
          Đã hoàn thành • Đúng hạn
        </Tag>
      );
    }
    if (isCompletedLate) {
      return (
        <Tag color="cyan" icon={<CheckCircleOutlined />} className="text-xs rounded-md font-semibold">
          Đã hoàn thành • Nộp trễ
        </Tag>
      );
    }
    if (isOverdue) {
      return (
        <Tag color="error" icon={<WarningOutlined />} className="text-xs rounded-md font-semibold">
          {isInProgress ? 'Quá hạn (Làm dở)' : 'Quá hạn nộp'}
        </Tag>
      );
    }
    if (isInProgress) {
      return (
        <Tag color="warning" icon={<ClockCircleOutlined />} className="text-xs rounded-md font-semibold">
          Đang làm dở
        </Tag>
      );
    }
    return (
      <Tag color="blue" icon={<ClockCircleOutlined />} className="text-xs rounded-md font-semibold">
        Chưa nộp bài
      </Tag>
    );
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 w-full space-y-6">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Breadcrumb
          items={[
            {
              title: (
                <span
                  onClick={() => navigate('/dashboard/my-homeworks')}
                  className="cursor-pointer text-gray-500 hover:text-indigo-600 transition-colors"
                >
                  Bài tập của tôi
                </span>
              ),
            },
            {
              title: (
                <span className="font-semibold text-gray-800 dark:text-gray-200 truncate max-w-[280px]">
                  {homework.title}
                </span>
              ),
            },
          ]}
        />

        <Space>
          {!isCompleted && (
            <Button
              icon={<SyncOutlined spin={isSyncing} />}
              loading={isSyncing}
              onClick={handleSync}
              className="rounded-lg font-medium border-blue-200 text-blue-600 hover:border-blue-500"
            >
              Đồng bộ từ Quiz
            </Button>
          )}
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/dashboard/my-homeworks')}
            className="rounded-lg font-medium"
          >
            Quay lại
          </Button>
        </Space>
      </div>

      {/* Main Header Card */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white dark:bg-zinc-800 border border-gray-100 dark:border-zinc-700 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xl">
                <BookOutlined />
              </div>
              <Title level={4} className="!mb-0 !text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
                {homework.title}
              </Title>
              {renderStatusTag()}
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 flex-wrap pt-1">
              {deadlineObj && (
                <span className="flex items-center gap-1.5">
                  <CalendarOutlined className="text-indigo-500" />
                  <b>Hạn nộp cá nhân:</b> {deadlineObj.format('DD/MM/YYYY HH:mm')} ({deadlineObj.fromNow()})
                </span>
              )}
              {homework.completed_at && (
                <span className="flex items-center gap-1.5 text-emerald-600">
                  <CheckCircleOutlined />
                  <b>Mốc hoàn thành:</b> {dayjs(homework.completed_at).format('DD/MM/YYYY HH:mm')}
                </span>
              )}
              {homework.last_synced_at && (
                <span className="flex items-center gap-1.5">
                  <SyncOutlined />
                  <b>Đồng bộ gần nhất:</b> {dayjs(homework.last_synced_at).format('DD/MM/YYYY HH:mm')}
                </span>
              )}
            </div>
          </div>

          {homework.link && (
            <Button
              type="primary"
              href={homework.link}
              target="_blank"
              rel="noopener noreferrer"
              icon={<ExportOutlined />}
              className="bg-indigo-600 hover:bg-indigo-700 rounded-xl font-semibold h-10 px-5 shadow-xs"
            >
              {isCompleted ? 'Xem bài trên Quiz' : 'Làm bài trên Quiz ngay'}
            </Button>
          )}
        </div>

        {/* Requirements Alert Banner */}
        <Alert
          type={isCompleted ? 'success' : 'info'}
          showIcon
          icon={<ThunderboltOutlined className={isCompleted ? 'text-emerald-600' : 'text-indigo-600'} />}
          className="text-xs rounded-xl"
          message={
            <span className="text-gray-800 dark:text-gray-200">
              <b>Tiêu chuẩn hoàn thành:</b>{' '}
              {hasBoth &&
                `Hoàn thành đủ ${homework.total_coding_required ?? codingExercises.length} bài tập Coding và Game trắc nghiệm.`}
              {hasOnlyCoding &&
                `Hoàn thành đạt đủ ${homework.total_coding_required ?? codingExercises.length} bài tập Coding trên hệ thống Quiz.`}
              {hasOnlyGame && 'Hoàn thành đạt bài tập Game trắc nghiệm.'}
              {!isCompleted && homework.uncompleted_items && homework.uncompleted_items.length > 0 && (
                <span className="ml-2 font-semibold text-amber-700">
                  • Còn thiếu: {homework.uncompleted_items.join(', ')}.
                </span>
              )}
            </span>
          }
        />
      </div>

      {/* Main Submissions Area */}
      <Card className="rounded-2xl border border-gray-100 dark:border-zinc-700 shadow-xs bg-white dark:bg-zinc-800">
        {hasBoth ? (
          <Tabs
            defaultActiveKey="coding"
            items={[
              {
                key: 'coding',
                label: (
                  <span className="flex items-center gap-2 font-semibold text-sm">
                    <CodeOutlined className="text-indigo-600" />
                    Bài tập Coding
                    <Tag
                      color={homework.coding_submitted ? 'success' : codingSubmissions.length > 0 ? 'warning' : 'default'}
                      className="m-0 text-xs rounded-md"
                    >
                      {homework.total_coding_completed ?? 0}/{homework.total_coding_required ?? 0} bài đạt
                    </Tag>
                  </span>
                ),
                children: (
                  <div className="pt-2">
                    <MyHomeworkExerciseChecklist exercises={codingExercises} />
                    <UnifiedSubmissionTimeline
                      submissions={codingSubmissions}
                      type="CODING"
                      deadline={homework.deadline}
                      homeworkLink={homework.link}
                      showExerciseOverview={false}
                      allExercises={timelineExercises}
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
                    {homework.game_submitted ? (
                      <Tag color={homework.game_is_late ? 'cyan' : 'success'} className="m-0 text-xs rounded-md">
                        {homework.game_is_late ? 'Hoàn thành (Trễ)' : 'Đã hoàn thành'}
                      </Tag>
                    ) : (
                      <Tag color="default" className="m-0 text-xs rounded-md">
                        Chưa hoàn thành
                      </Tag>
                    )}
                  </span>
                ),
                children: (
                  <div className="pt-2">
                    <UnifiedSubmissionTimeline
                      submissions={gameSubmissions}
                      type="GAME"
                      deadline={homework.deadline}
                      homeworkLink={homework.link}
                      showExerciseOverview={false}
                    />
                  </div>
                ),
              },
            ]}
          />
        ) : hasOnlyCoding ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-gray-100 dark:border-zinc-700">
              <CodeOutlined className="text-indigo-600 text-lg" />
              <Title level={5} className="!mb-0 font-bold text-gray-800 dark:text-gray-100">
                Tiến độ & lịch sử nộp bài tập Coding
              </Title>
            </div>
            <MyHomeworkExerciseChecklist exercises={codingExercises} />
            <UnifiedSubmissionTimeline
              submissions={codingSubmissions}
              type="CODING"
              deadline={homework.deadline}
              homeworkLink={homework.link}
              showExerciseOverview={false}
              allExercises={timelineExercises}
            />
          </div>
        ) : hasOnlyGame ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-gray-100 dark:border-zinc-700">
              <TrophyOutlined className="text-purple-600 text-lg" />
              <Title level={5} className="!mb-0 font-bold text-gray-800 dark:text-gray-100">
                Lịch sử chơi Game Quiz trắc nghiệm
              </Title>
            </div>
            <UnifiedSubmissionTimeline
              submissions={gameSubmissions}
              type="GAME"
              deadline={homework.deadline}
              homeworkLink={homework.link}
              showExerciseOverview={false}
            />
          </div>
        ) : (
          <UnifiedSubmissionTimeline
            submissions={codingSubmissions}
            type="CODING"
            deadline={homework.deadline}
            homeworkLink={homework.link}
            showExerciseOverview={false}
            allExercises={timelineExercises}
          />
        )}
      </Card>
    </div>
  );
};

export default MyHomeworkDetailPage;
