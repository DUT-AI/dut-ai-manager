import React, { useMemo } from 'react';
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
  Alert,
  Breadcrumb,
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
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import { useHomework, useMyHomeworkSubmissions } from '../hooks/useHomeworks';
import { UnifiedSubmissionTimeline } from '../components/UnifiedSubmissionTimeline';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Title, Text } = Typography;

export const MyHomeworkDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const homeworkId = id ? Number(id) : null;

  const { data: homework, isLoading: isHwLoading } = useHomework(homeworkId);
  const { data: submissions = [], isLoading: isSubLoading } = useMyHomeworkSubmissions(homeworkId);

  const isLoading = isHwLoading || isSubLoading;
  const deadlineObj = homework ? dayjs(homework.deadline) : null;
  const isOverdue = deadlineObj ? dayjs().isAfter(deadlineObj) : false;

  const requiresCoding = homework?.requires_coding ?? true;
  const requiresGame = homework?.requires_game ?? false;

  const hasBoth = requiresCoding && requiresGame;
  const hasOnlyCoding = requiresCoding && !requiresGame;
  const hasOnlyGame = !requiresCoding && requiresGame;

  // Filter submissions
  const codingSubmissions = useMemo(
    () => (submissions || []).filter((s) => s.submission_type === 'CODING'),
    [submissions]
  );
  const gameSubmissions = useMemo(
    () => (submissions || []).filter((s) => s.submission_type === 'GAME'),
    [submissions]
  );

  const isCodingSubmitted = codingSubmissions.length > 0;
  const isGameSubmitted = gameSubmissions.length > 0;
  const isFullyPassed = hasBoth
    ? isCodingSubmitted && isGameSubmitted
    : hasOnlyCoding
      ? isCodingSubmitted
      : isGameSubmitted;

  if (isLoading && !homework) {
    return (
      <div className="p-8 flex flex-col justify-center items-center gap-3 min-h-[60vh]">
        <Spin size="large" />
        <Text type="secondary" className="text-sm">Đang tải lịch sử làm bài...</Text>
      </div>
    );
  }

  if (!homework) {
    return (
      <div className="p-8">
        <Empty description="Không tìm thấy bài tập yêu cầu">
          <Button type="primary" onClick={() => navigate('/dashboard/my-homeworks')}>
            Quay lại Bài tập của tôi
          </Button>
        </Empty>
      </div>
    );
  }

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

        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard/my-homeworks')}
          className="rounded-lg font-medium"
        >
          Quay lại
        </Button>
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
              {isFullyPassed ? (
                <Tag color="success" icon={<CheckCircleOutlined />} className="text-xs rounded-md font-semibold">
                  Đã hoàn thành
                </Tag>
              ) : isOverdue ? (
                <Tag color="error" icon={<WarningOutlined />} className="text-xs rounded-md font-semibold">
                  Quá hạn nộp
                </Tag>
              ) : (
                <Tag color="blue" icon={<ClockCircleOutlined />} className="text-xs rounded-md font-semibold">
                  Đang diễn ra
                </Tag>
              )}
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 flex-wrap pt-1">
              {deadlineObj && (
                <span className="flex items-center gap-1.5">
                  <CalendarOutlined className="text-indigo-500" />
                  <b>Hạn nộp:</b> {deadlineObj.format('DD/MM/YYYY HH:mm')} ({deadlineObj.fromNow()})
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
              Làm bài trên Quiz ngay
            </Button>
          )}
        </div>

        {/* Requirements Alert Banner */}
        <Alert
          type="info"
          showIcon
          icon={<ThunderboltOutlined className="text-indigo-600" />}
          className="text-xs rounded-xl bg-indigo-50/60 dark:bg-indigo-950/40 border-indigo-100 dark:border-indigo-900/50"
          message={
            <span className="text-gray-800 dark:text-gray-200">
              <b>Tiêu chuẩn hoàn thành:</b>{' '}
              {hasBoth && 'Nộp file bài tập Coding và Hoàn thành Game trắc nghiệm (đúng 100%).'}
              {hasOnlyCoding && 'Nộp file bài tập Coding thành công lên hệ thống Quiz.'}
              {hasOnlyGame && 'Hoàn thành Game trắc nghiệm đúng 100% câu hỏi.'}
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
                    {isCodingSubmitted ? (
                      <Tag color="success" className="m-0 text-xs rounded-md">
                        {codingSubmissions.length} lần nộp
                      </Tag>
                    ) : (
                      <Tag color="default" className="m-0 text-xs rounded-md">
                        Chưa nộp
                      </Tag>
                    )}
                  </span>
                ),
                children: (
                  <div className="pt-2">
                    <UnifiedSubmissionTimeline
                      submissions={codingSubmissions}
                      type="CODING"
                      deadline={homework.deadline}
                      homeworkLink={homework.link}
                      showExerciseOverview={true}
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
                    {isGameSubmitted ? (
                      <Tag color="success" className="m-0 text-xs rounded-md">
                        Đã xong 100%
                      </Tag>
                    ) : (
                      <Tag color="default" className="m-0 text-xs rounded-md">
                        Chưa xong
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
                Lịch sử nộp bài tập Coding
              </Title>
            </div>
            <UnifiedSubmissionTimeline
              submissions={codingSubmissions}
              type="CODING"
              deadline={homework.deadline}
              homeworkLink={homework.link}
              showExerciseOverview={true}
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
            showExerciseOverview={true}
          />
        )}
      </Card>
    </div>
  );
};
export default MyHomeworkDetailPage;
