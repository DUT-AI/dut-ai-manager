import { useState, useEffect, useCallback, useRef } from 'react';
import {
    Typography,
    Space,
} from 'antd';
import {
    LineChartOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportService } from '@/features/academic-report/services/report.service';
import type { ActivityTrendItem } from '@/features/academic-report/types/report.types';
import { motion, type Variants } from 'motion/react';
import { Agentation } from 'agentation';

import {
    ResponsiveContainer,
    ComposedChart,
    Bar,
    Line,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip as RechartsTooltip,
    Legend
} from 'recharts';

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' },
    },
};

const CustomChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;

    const uniquePayload = payload.filter((entry: any, index: number, self: any[]) =>
        index === self.findIndex((e: any) => e.dataKey === entry.dataKey)
    );

    return (
        <div className="bg-white p-3 rounded-xl shadow-lg border border-gray-100">
            <Text strong className="text-xs block mb-2">{label}</Text>
            {uniquePayload.map((entry: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-gray-500">{entry.name}:</span>
                    <span className="font-semibold">{entry.value}</span>
                </div>
            ))}
        </div>
    );
};

const CustomOffsetDot = (props: any) => {
    const { cx, cy, stroke, value, offset, r, fill, strokeWidth } = props;
    if (value === null || value === undefined) return null;
    return (
        <circle cx={cx + offset} cy={cy} r={r || 4} stroke={stroke} strokeWidth={strokeWidth || 2} fill={fill || "white"} />
    );
};

const ActivityTrendPage = () => {
    const [allData, setAllData] = useState<ActivityTrendItem[]>([]);
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    const fetchTrend = useCallback(async () => {
        setLoading(true);
        try {
            const now = dayjs();
            const data = await reportService.getActivityTrend(
                now.month() + 1,
                now.year(),
                'week'
            );
            setAllData(data || []);
        } catch (error) {
            console.error('Failed to fetch activity trend:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTrend();
    }, [fetchTrend]);

    // Drag to paginate logic
    const [offset, setOffset] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [startX, setStartX] = useState(0);

    const WEEKS_TO_SHOW = 8;
    const SHIFT_STEP = 4;
    const maxOffset = Math.max(0, allData.length - WEEKS_TO_SHOW);

    const endIndex = allData.length - offset;
    const startIndex = Math.max(0, endIndex - WEEKS_TO_SHOW);
    const currentData = allData.slice(startIndex, endIndex);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        setStartX(e.pageX);
    };

    const handleMouseLeave = () => {
        setIsDragging(false);
    };

    const handleMouseUp = (e: React.MouseEvent) => {
        if (!isDragging) return;
        setIsDragging(false);
        const walk = e.pageX - startX;

        if (walk > 50 && offset < maxOffset) {
            setOffset(prev => Math.min(maxOffset, prev + SHIFT_STEP)); // Swipe Right -> Older
        } else if (walk < -50 && offset > 0) {
            setOffset(prev => Math.max(0, prev - SHIFT_STEP)); // Swipe Left -> Newer
        }
    };

    return (
        <div className="w-full">
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="w-full"
            >
                <motion.div
                    variants={itemVariants}
                    className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4"
                >
                    <div>
                        <Text type="secondary" className="text-xs md:text-sm">
                            Biến động điểm cộng & vi phạm qua các tuần (Vuốt ngang trên biểu đồ để xem lịch sử cũ hơn)
                        </Text>
                    </div>
                </motion.div>

                <motion.div
                    variants={itemVariants}
                    className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm w-full mb-8"
                >
                    <div
                        ref={scrollRef}
                        className={`h-96 w-full overflow-hidden ${isDragging ? 'cursor-grabbing' : 'cursor-grab'} select-none`}
                        style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.3s' }}
                        onMouseDown={handleMouseDown}
                        onMouseLeave={handleMouseLeave}
                        onMouseUp={handleMouseUp}
                    >
                        {allData.length > 0 ? (
                            <div style={{ width: '100%', height: '100%', pointerEvents: isDragging ? 'none' : 'auto' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart data={currentData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                        <XAxis
                                            dataKey="label"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fontSize: 12, fill: '#94a3b8' }}
                                            dy={10}
                                        />
                                        {/* Left Y-axis: Bonus Points */}
                                        <YAxis
                                            yAxisId="bonus"
                                            orientation="left"
                                            domain={[0, 'dataMax']}
                                            tickFormatter={(v: number) => `+${v}`}
                                            stroke="#22c55e"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fontSize: 12, fill: '#22c55e' }}
                                        />
                                        {/* Right Y-axis: Violations */}
                                        <YAxis
                                            yAxisId="violation"
                                            orientation="right"
                                            domain={[0, 'dataMax']}
                                            stroke="#ef4444"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fontSize: 12, fill: '#ef4444' }}
                                        />
                                        <RechartsTooltip content={<CustomChartTooltip />} />
                                        <Legend
                                            iconType="circle"
                                            wrapperStyle={{ fontSize: '13px', paddingTop: '16px' }}
                                        />
                                        <Bar
                                            yAxisId="bonus"
                                            dataKey="total_bonus_points"
                                            name="Điểm cộng"
                                            fill="#22c55e"
                                            radius={[4, 4, 0, 0]}
                                            barSize={24}
                                        />
                                        <Bar
                                            yAxisId="violation"
                                            dataKey="violation_count"
                                            name="Vi phạm"
                                            fill="#ef4444"
                                            radius={[4, 4, 0, 0]}
                                            barSize={24}
                                        />
                                        <Line
                                            yAxisId="bonus"
                                            type="monotone"
                                            dataKey="total_bonus_points"
                                            name="Điểm cộng"
                                            stroke="#16a34a"
                                            strokeWidth={2}
                                            dot={<CustomOffsetDot offset={-12} />}
                                            activeDot={<CustomOffsetDot offset={-12} r={6} stroke="#16a34a" />}
                                            legendType="none"
                                        />
                                        <Line
                                            yAxisId="violation"
                                            type="monotone"
                                            dataKey="violation_count"
                                            name="Vi phạm"
                                            stroke="#dc2626"
                                            strokeWidth={2}
                                            dot={<CustomOffsetDot offset={12} />}
                                            activeDot={<CustomOffsetDot offset={12} r={6} stroke="#dc2626" />}
                                            legendType="none"
                                        />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">
                                <Text type="secondary">Chưa có dữ liệu cho khoảng thời gian này</Text>
                            </div>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </div>
    );
};

export default ActivityTrendPage;
