import React from 'react';
import { Col, Row, Typography } from 'antd';
import type { MyHomeworksStats } from '../types/homework.types';

const { Text } = Typography;

export interface MyHomeworkStatsCardsProps {
    stats: MyHomeworksStats;
}

export const MyHomeworkStatsCards: React.FC<MyHomeworkStatsCardsProps> = ({ stats }) => {
    const completedLate = stats.completed_late ?? 0;
    const completedOnTime = stats.completed_on_time ?? 0;

    return (
        <Row gutter={[16, 16]}>
            <Col xs={12} sm={6}>
                <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-50/70 via-indigo-50/30 to-slate-50 border border-indigo-100/70 shadow-2xs hover:shadow-xs transition-all h-full">
                    <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-indigo-600/80">
                        Tất cả bài tập
                    </Text>
                    <div className="text-2xl sm:text-3xl font-extrabold text-indigo-700 mt-1">
                        {stats.total ?? 0}
                    </div>
                </div>
            </Col>
            <Col xs={12} sm={6}>
                <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50/70 via-emerald-50/30 to-teal-50/30 border border-emerald-100/70 shadow-2xs hover:shadow-xs transition-all h-full">
                    <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-emerald-600/80">
                        Đã hoàn thành
                    </Text>
                    <div className="text-2xl sm:text-3xl font-extrabold text-emerald-600 mt-1">
                        {stats.completed ?? 0}
                    </div>
                    {completedLate > 0 && (
                        <Text type="secondary" className="text-[11px] block mt-0.5">
                            {completedOnTime} đúng hạn • {completedLate} nộp trễ
                        </Text>
                    )}
                </div>
            </Col>
            <Col xs={12} sm={6}>
                <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-50/70 via-amber-50/30 to-yellow-50/30 border border-amber-100/70 shadow-2xs hover:shadow-xs transition-all h-full">
                    <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-amber-600/80">
                        Chưa hoàn thành
                    </Text>
                    <div className="text-2xl sm:text-3xl font-extrabold text-amber-600 mt-1">
                        {stats.uncompleted ?? 0}
                    </div>
                </div>
            </Col>
            <Col xs={12} sm={6}>
                <div className="p-4 rounded-2xl bg-gradient-to-br from-rose-50/70 via-rose-50/30 to-pink-50/30 border border-rose-100/70 shadow-2xs hover:shadow-xs transition-all h-full">
                    <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-rose-600/80">
                        Quá hạn chưa xong
                    </Text>
                    <div className="text-2xl sm:text-3xl font-extrabold text-rose-600 mt-1">
                        {stats.overdue ?? 0}
                    </div>
                </div>
            </Col>
        </Row>
    );
};

export default MyHomeworkStatsCards;
