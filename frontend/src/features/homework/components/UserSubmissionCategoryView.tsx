import React, { useState, useMemo } from 'react';
import { Input, Tabs, Segmented, Spin, Empty, Button } from 'antd';
import {
    SearchOutlined,
    FilterOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined
} from '@ant-design/icons';
import type { UserSubmissionInfo } from '@/features/homework/types/homework.types';
import { UserSubmissionCard } from './UserSubmissionCard';

export interface UserSubmissionCategoryViewProps {
    status?: { submitted: UserSubmissionInfo[]; not_submitted: UserSubmissionInfo[] };
    isLoading: boolean;
    isOverdue?: boolean;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}

export const UserSubmissionCategoryView: React.FC<UserSubmissionCategoryViewProps> = ({
    status,
    isLoading,
    onViewHistory
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [subTab, setSubTab] = useState<'submitted' | 'not_submitted'>('submitted');
    const [submittedFilter, setSubmittedFilter] = useState<'all' | 'on_time' | 'late'>('all');

    const submitted = useMemo(() => status?.submitted ?? [], [status?.submitted]);
    const notSubmitted = useMemo(() => status?.not_submitted ?? [], [status?.not_submitted]);

    // Lọc danh sách Đã nộp theo Search & Filter Status
    const filteredSubmitted = useMemo(() => {
        return submitted.filter((u) => {
            const query = searchQuery.trim().toLowerCase();
            const matchesSearch = query
                ? (u.name?.toLowerCase().includes(query) || String(u.user_id).includes(query))
                : true;
            if (!matchesSearch) return false;

            if (submittedFilter === 'late') return !!u.is_late;
            if (submittedFilter === 'on_time') return !u.is_late;
            return true;
        });
    }, [submitted, searchQuery, submittedFilter]);

    // Lọc danh sách Chưa nộp theo Search
    const filteredNotSubmitted = useMemo(() => {
        return notSubmitted.filter((u) => {
            const query = searchQuery.trim().toLowerCase();
            return query
                ? (u.name?.toLowerCase().includes(query) || String(u.user_id).includes(query))
                : true;
        });
    }, [notSubmitted, searchQuery]);

    const lateCount = useMemo(() => submitted.filter(u => u.is_late).length, [submitted]);
    const onTimeCount = submitted.length - lateCount;

    return (
        <div className="flex flex-col gap-3 pt-1">
            {/* Search Input Bar */}
            <div className="flex items-center gap-2">
                <Input
                    prefix={<SearchOutlined className="text-gray-400" />}
                    placeholder="Tìm kiếm theo tên hoặc ID học viên..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    allowClear
                    className="rounded-lg text-sm bg-gray-50/70 dark:bg-zinc-800/80 border-gray-200 dark:border-zinc-700"
                />
            </div>

            {/* Sub-tabs: Đã nộp / Chưa nộp */}
            <div className="border-b border-gray-100 dark:border-zinc-800">
                <Tabs
                    activeKey={subTab}
                    onChange={(val) => setSubTab(val as 'submitted' | 'not_submitted')}
                    size="small"
                    className="submission-subtabs"
                    items={[
                        {
                            key: 'submitted',
                            label: (
                                <span className="flex items-center gap-1.5 font-medium text-xs pb-0.5">
                                    <CheckCircleOutlined className="text-emerald-500 text-sm" />
                                    <span>Đã nộp</span>
                                    <span className="inline-flex items-center justify-center min-w-[20px] px-1.5 py-0.2 text-[11px] font-semibold rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/60 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800/60">
                                        {submitted.length}
                                    </span>
                                </span>
                            ),
                        },
                        {
                            key: 'not_submitted',
                            label: (
                                <span className="flex items-center gap-1.5 font-medium text-xs pb-0.5">
                                    <CloseCircleOutlined className="text-rose-500 text-sm" />
                                    <span>Chưa nộp</span>
                                    <span className="inline-flex items-center justify-center min-w-[20px] px-1.5 py-0.2 text-[11px] font-semibold rounded-full bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-950/60 dark:text-rose-400 dark:border-rose-800/60">
                                        {notSubmitted.length}
                                    </span>
                                </span>
                            ),
                        },
                    ]}
                />
            </div>

            {/* Bộ lọc trạng thái (hiển thị hàng dưới tách biệt) */}
            {subTab === 'submitted' && submitted.length > 0 && (
                <div className="flex items-center justify-between gap-2 px-2.5 py-1.5 bg-gray-50/70 dark:bg-zinc-800/60 rounded-xl border border-gray-100/80 dark:border-zinc-700/60">
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1.5 font-medium">
                        <FilterOutlined className="text-indigo-500 text-xs" /> Trạng thái bài nộp:
                    </span>
                    <Segmented
                        size="small"
                        value={submittedFilter}
                        onChange={(val) => setSubmittedFilter(val as 'all' | 'on_time' | 'late')}
                        options={[
                            { label: `Tất cả (${submitted.length})`, value: 'all' },
                            { label: `Đúng hạn (${onTimeCount})`, value: 'on_time' },
                            { label: `Nộp trễ (${lateCount})`, value: 'late' },
                        ]}
                        className="bg-white dark:bg-zinc-700/80 text-xs rounded-lg shadow-2xs"
                    />
                </div>
            )}

            {/* Search query tag result notification */}
            {searchQuery.trim() && (
                <div className="flex items-center justify-between text-xs text-gray-500 bg-indigo-50/60 dark:bg-indigo-950/40 px-3 py-1.5 rounded-lg">
                    <span>
                        Kết quả cho: <b className="text-indigo-600 dark:text-indigo-400">"{searchQuery.trim()}"</b>
                    </span>
                    <span className="font-medium">
                        {subTab === 'submitted' ? filteredSubmitted.length : filteredNotSubmitted.length} học viên
                    </span>
                </div>
            )}

            {/* List Body */}
            <div className="min-h-[220px]">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-16 gap-2 text-gray-400">
                        <Spin size="default" />
                        <span className="text-xs">Đang tải danh sách bài nộp...</span>
                    </div>
                ) : subTab === 'submitted' ? (
                    filteredSubmitted.length === 0 ? (
                        <div className="py-12 flex flex-col items-center justify-center">
                            <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description={
                                    searchQuery.trim()
                                        ? `Không tìm thấy học viên đã nộp nào khớp với "${searchQuery}"`
                                        : "Chưa có học viên nào nộp bài"
                                }
                            />
                            {searchQuery.trim() && (
                                <Button
                                    size="small"
                                    onClick={() => setSearchQuery('')}
                                    className="mt-2 text-xs"
                                >
                                    Xóa tìm kiếm
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col">
                            {filteredSubmitted.map((user) => (
                                <UserSubmissionCard
                                    key={user.user_id}
                                    user={user}
                                    isSubmitted={true}
                                    onViewHistory={onViewHistory}
                                />
                            ))}
                        </div>
                    )
                ) : (
                    filteredNotSubmitted.length === 0 ? (
                        <div className="py-12 flex flex-col items-center justify-center">
                            <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description={
                                    searchQuery.trim()
                                        ? `Không tìm thấy học viên chưa nộp nào khớp với "${searchQuery}"`
                                        : "Tất cả học viên đều đã nộp bài 🎉"
                                }
                            />
                            {searchQuery.trim() && (
                                <Button
                                    size="small"
                                    onClick={() => setSearchQuery('')}
                                    className="mt-2 text-xs"
                                >
                                    Xóa tìm kiếm
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col">
                            {filteredNotSubmitted.map((user) => (
                                <UserSubmissionCard
                                    key={user.user_id}
                                    user={user}
                                    isSubmitted={false}
                                    onViewHistory={onViewHistory}
                                />
                            ))}
                        </div>
                    )
                )}
            </div>
        </div>
    );
};
