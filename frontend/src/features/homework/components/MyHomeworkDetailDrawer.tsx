import React from 'react';
import {
    Drawer,
    Tabs,
    Tag,
    Typography,
    Empty,
    Spin,
    Button,
    Grid,
    Alert,
} from 'antd';
import {
    CodeOutlined,
    TrophyOutlined,
    ClockCircleOutlined,
    ExportOutlined,
    CalendarOutlined,
    ThunderboltOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import { useHomework, useMyHomeworkSubmissions } from '../hooks/useHomeworks';
import { MySubmissionTimeline } from './MySubmissionTimeline';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

interface MyHomeworkDetailDrawerProps {
    homeworkId: number | null;
    open: boolean;
    onClose: () => void;
}

export const MyHomeworkDetailDrawer: React.FC<MyHomeworkDetailDrawerProps> = ({
    homeworkId,
    open,
    onClose,
}) => {
    const screens = useBreakpoint();

    const { data: homework, isLoading: isHwLoading } = useHomework(open ? homeworkId : null);
    const { data: submissions = [], isLoading: isSubLoading } = useMyHomeworkSubmissions(
        open ? homeworkId : null
    );

    const isLoading = isHwLoading || isSubLoading;

    const deadlineObj = homework ? dayjs(homework.deadline) : null;
    const isOverdue = deadlineObj ? dayjs().isAfter(deadlineObj) : false;

    // Lọc theo yêu cầu của bài tập:
    // requires_coding: có phần Coding hay không
    // requires_game: có phần Game hay không
    const requiresCoding = homework?.requires_coding ?? true;
    const requiresGame = homework?.requires_game ?? false;

    const hasBoth = requiresCoding && requiresGame;
    const hasOnlyCoding = requiresCoding && !requiresGame;
    const hasOnlyGame = !requiresCoding && requiresGame;

    // Phân loại submissions
    const codingSubmissions = submissions.filter((s) => s.submission_type === 'CODING');
    const gameSubmissions = submissions.filter((s) => s.submission_type === 'GAME');

    return (
        <Drawer
            title={
                <div className="flex flex-col gap-1 pr-2">
                    <span className="font-bold text-base leading-snug line-clamp-1 text-gray-900">
                        {homework?.title || 'Chi tiết bài tập'}
                    </span>
                    <div className="flex items-center gap-2 flex-wrap">
                        {deadlineObj && (
                            <span className="inline-flex items-center gap-1 text-xs text-gray-500 font-normal">
                                <CalendarOutlined className="text-gray-400" />
                                Hạn nộp: {deadlineObj.format('DD/MM/YYYY HH:mm')}
                            </span>
                        )}
                        {isOverdue ? (
                            <Tag color="red" icon={<WarningOutlined />} className="text-xs m-0 font-medium">
                                Quá hạn
                            </Tag>
                        ) : (
                            <Tag color="blue" icon={<ClockCircleOutlined />} className="text-xs m-0 font-medium">
                                Đang mở
                            </Tag>
                        )}
                    </div>
                </div>
            }
            extra={
                homework?.link ? (
                    <Button
                        type="primary"
                        href={homework.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        icon={<ExportOutlined />}
                        size="small"
                        className="bg-indigo-600 hover:bg-indigo-700 font-semibold"
                    >
                        Làm bài Quiz
                    </Button>
                ) : null
            }
            placement="right"
            width={screens.md ? 520 : '100%'}
            open={open}
            onClose={onClose}
            styles={{ body: { padding: '16px 20px' } }}
        >
            {isLoading ? (
                <div className="py-20 flex flex-col justify-center items-center gap-3">
                    <Spin size="large" />
                    <Text type="secondary" className="text-xs">Đang tải lịch sử làm bài...</Text>
                </div>
            ) : !homework ? (
                <Empty description="Không tìm thấy thông tin bài tập" />
            ) : (
                <div className="space-y-4">
                    {/* Yêu cầu nộp bài Alert */}
                    <Alert
                        type="info"
                        showIcon
                        icon={<ThunderboltOutlined />}
                        className="text-xs rounded-xl"
                        message={
                            <span>
                                Tiêu chuẩn hoàn thành:
                                {hasBoth && (
                                    <b> Nộp file Coding và Hoàn thành Game trắc nghiệm (đúng 100%).</b>
                                )}
                                {hasOnlyCoding && <b> Nộp file bài tập Coding thành công.</b>}
                                {hasOnlyGame && <b> Hoàn thành Game trắc nghiệm đúng 100% câu hỏi.</b>}
                            </span>
                        }
                    />

                    {/* HIỂN THỊ THEO YÊU CẦU BÀI TẬP: */}
                    {hasBoth ? (
                        /* Trường hợp có CẢ HAI: Hiển thị 2 Tab Coding & Game */
                        <Tabs
                            defaultActiveKey="coding"
                            items={[
                                {
                                    key: 'coding',
                                    label: (
                                        <span className="flex items-center gap-1.5 font-semibold">
                                            <CodeOutlined />
                                            Bài tập Coding
                                            {codingSubmissions.length > 0 ? (
                                                <Tag color="success" className="m-0 text-[10px] ml-1">Đã nộp</Tag>
                                            ) : (
                                                <Tag color="default" className="m-0 text-[10px] ml-1">Chưa nộp</Tag>
                                            )}
                                        </span>
                                    ),
                                    children: (
                                        <MySubmissionTimeline
                                            submissions={codingSubmissions}
                                            type="CODING"
                                            deadline={homework.deadline}
                                            homeworkLink={homework.link}
                                        />
                                    ),
                                },
                                {
                                    key: 'game',
                                    label: (
                                        <span className="flex items-center gap-1.5 font-semibold">
                                            <TrophyOutlined />
                                            Trắc nghiệm Game
                                            {gameSubmissions.length > 0 ? (
                                                <Tag color="success" className="m-0 text-[10px] ml-1">Đã xong</Tag>
                                            ) : (
                                                <Tag color="default" className="m-0 text-[10px] ml-1">Chưa xong</Tag>
                                            )}
                                        </span>
                                    ),
                                    children: (
                                        <MySubmissionTimeline
                                            submissions={gameSubmissions}
                                            type="GAME"
                                            deadline={homework.deadline}
                                            homeworkLink={homework.link}
                                        />
                                    ),
                                },
                            ]}
                        />
                    ) : hasOnlyCoding ? (
                        /* Trường hợp CHỈ CÓ Coding: Chỉ hiển thị 1 SubmissionType Coding */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <CodeOutlined className="text-indigo-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử nộp bài Coding
                                </Title>
                            </div>
                            <MySubmissionTimeline
                                submissions={codingSubmissions}
                                type="CODING"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    ) : hasOnlyGame ? (
                        /* Trường hợp CHỈ CÓ Game: Chỉ hiển thị 1 SubmissionType Game */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <TrophyOutlined className="text-purple-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử chơi Game trắc nghiệm
                                </Title>
                            </div>
                            <MySubmissionTimeline
                                submissions={gameSubmissions}
                                type="GAME"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    ) : (
                        /* Fallback nếu không cấu hình: hiển thị Coding */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <CodeOutlined className="text-indigo-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử nộp bài tập
                                </Title>
                            </div>
                            <MySubmissionTimeline
                                submissions={codingSubmissions}
                                type="CODING"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    )}
                </div>
            )}
        </Drawer>
    );
};

export default MyHomeworkDetailDrawer;
