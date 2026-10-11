import React, { useMemo } from 'react';
import { Spin, Empty } from 'antd';
import { useMeetingEvaluationSummary } from '../hooks/useMeetings';
import type { CriteriaBreakdown } from '../types/meeting.types';
import { TRAINER_TO_TRAINEE_CODES } from './summary/evaluationConstants';
import {
  MeetingOverallEvaluationCard,
  EvaluationOverviewCards,
  EvaluationCriteriaBreakdownCards,
  EvaluationFeedbackListCard,
} from './summary';

interface Props {
  meetingId: number;
}

export const MeetingEvaluationSummaryView: React.FC<Props> = ({ meetingId }) => {
  const { data: summary, isLoading: loading } = useMeetingEvaluationSummary(meetingId, true);

  const {
    trainerCriteria,
    traineeCriteria,
    trainerAvgScore,
    traineeAvgScore,
    trainerCount,
    traineeCount,
  } = useMemo(() => {
    if (!summary) {
      return {
        trainerCriteria: [],
        traineeCriteria: [],
        trainerAvgScore: 0,
        traineeAvgScore: 0,
        trainerCount: 0,
        traineeCount: 0,
      };
    }

    const trainerList: CriteriaBreakdown[] = [];
    const traineeList: CriteriaBreakdown[] = [];

    summary.criteria_breakdown.forEach((item) => {
      if (
        item.evaluation_type === 'TRAINER_TO_TRAINEE' ||
        TRAINER_TO_TRAINEE_CODES.has(item.criteria_code)
      ) {
        trainerList.push(item);
      } else {
        traineeList.push(item);
      }
    });

    const trainerEvals = summary.evaluations.filter(
      (e) => e.evaluation_type === 'TRAINER_TO_TRAINEE'
    );
    const traineeEvals = summary.evaluations.filter(
      (e) => e.evaluation_type === 'TRAINEE_TO_TRAINER'
    );

    const trainerAvg =
      summary.trainer_average_score ??
      (trainerEvals.length > 0
        ? Number(
            (
              trainerEvals.reduce((acc, curr) => acc + curr.average_score, 0) /
              trainerEvals.length
            ).toFixed(1)
          )
        : 0);

    const traineeAvg =
      summary.trainee_average_score ??
      (traineeEvals.length > 0
        ? Number(
            (
              traineeEvals.reduce((acc, curr) => acc + curr.average_score, 0) /
              traineeEvals.length
            ).toFixed(1)
          )
        : 0);

    return {
      trainerCriteria: trainerList,
      traineeCriteria: traineeList,
      trainerAvgScore: trainerAvg,
      traineeAvgScore: traineeAvg,
      trainerCount: summary.total_trainer_evaluations ?? trainerEvals.length,
      traineeCount: summary.total_trainee_evaluations ?? traineeEvals.length,
    };
  }, [summary]);

  if (loading) {
    return (
      <div className="text-center py-10">
        <Spin tip="Đang tải báo cáo đánh giá..." />
      </div>
    );
  }

  if (!summary || (summary.total_evaluations === 0 && !summary.overall_evaluation)) {
    return (
      <Empty
        description="Chưa có đánh giá nào cho buổi học này"
        className="py-6"
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* 1. Đánh giá tổng thể buổi học từ Trainer (Mô hình 1-1) */}
      {summary.overall_evaluation && (
        <MeetingOverallEvaluationCard overallEvaluation={summary.overall_evaluation} />
      )}

      {/* 2. Tổng quan điểm số (3 Card thống kê) */}
      <EvaluationOverviewCards
        summary={summary}
        trainerCount={trainerCount}
        traineeCount={traineeCount}
        trainerAvgScore={trainerAvgScore}
        traineeAvgScore={traineeAvgScore}
      />

      {/* 3. Chi tiết tiêu chí (2 Cột Trainer & Trainee) */}
      <EvaluationCriteriaBreakdownCards
        trainerCriteria={trainerCriteria}
        traineeCriteria={traineeCriteria}
      />

      {/* 4. Danh sách nhận xét & ý kiến đóng góp */}
      <EvaluationFeedbackListCard evaluations={summary.evaluations} />
    </div>
  );
};
