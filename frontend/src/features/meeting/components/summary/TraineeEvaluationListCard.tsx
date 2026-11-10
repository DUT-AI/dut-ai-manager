import React, { useState } from 'react';
import { Card, Table, Avatar, Typography, Tag, Rate, Button, Tooltip, Empty } from 'antd';
import { TeamOutlined, UserOutlined, EyeOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import type { EvaluationResponse } from '../../types/meeting.types';
import { EvaluationDetailModal } from '../EvaluationDetailModal';

const { Text } = Typography;

interface Props {
  evaluations: EvaluationResponse[];
}

export const TraineeEvaluationListCard: React.FC<Props> = ({ evaluations }) => {
  const [selectedEval, setSelectedEval] = useState<EvaluationResponse | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Chỉ lấy các đánh giá từ Trainee gửi cho Trainer
  const traineeEvaluations = evaluations.filter(
    (e) => e.evaluation_type === 'TRAINEE_TO_TRAINER'
  );

  const columns: ColumnsType<EvaluationResponse> = [
    {
      title: 'Học viên đánh giá',
      key: 'reviewer',
      render: (_: unknown, record: EvaluationResponse) => {
        const isAnon = record.is_anonymous;
        return (
          <div className="flex items-center gap-2.5">
            <Avatar
              icon={<UserOutlined />}
              src={isAnon ? null : record.reviewer?.avatar_url}
              size="default"
              style={{
                backgroundColor: isAnon ? '#8c8c8c' : '#1890ff',
              }}
            />
            <div>
              <div className="flex items-center gap-1.5">
                <Text strong className="text-sm text-gray-800">
                  {isAnon ? 'Học viên ẩn danh' : record.reviewer?.name || `User #${record.reviewer_id}`}
                </Text>
                {isAnon && <Tag color="purple" className="text-[10px] py-0 px-1 m-0">Ẩn danh</Tag>}
              </div>
              {!isAnon && record.reviewer_id && (
                <span className="text-[11px] text-gray-400">ID: #{record.reviewer_id}</span>
              )}
            </div>
          </div>
        );
      },
    },
    {
      title: 'Giảng viên được đánh giá',
      key: 'target_user',
      render: (_: unknown, record: EvaluationResponse) => (
        <div className="flex items-center gap-2">
          <Avatar
            icon={<UserOutlined />}
            src={record.target_user?.avatar_url}
            size="small"
            className="border border-amber-200"
          />
          <Text className="text-xs font-medium text-gray-700">
            {record.target_user?.name || `Trainer #${record.target_user_id}`}
          </Text>
        </div>
      ),
    },
    {
      title: 'Điểm đánh giá',
      key: 'average_score',
      dataIndex: 'average_score',
      sorter: (a, b) => a.average_score - b.average_score,
      render: (score: number) => (
        <div className="flex items-center gap-2">
          <Rate disabled allowHalf value={score} style={{ fontSize: 12 }} />
          <Tag color="gold" className="font-semibold text-xs py-0.5 px-1.5 m-0">
            {score.toFixed(1)}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Nhận xét',
      dataIndex: 'feedback_text',
      key: 'feedback_text',
      render: (text: string | null) => (
        <div className="max-w-xs truncate text-xs text-gray-600">
          {text ? text : <span className="text-gray-300 italic">Không có nhận xét</span>}
        </div>
      ),
    },
    {
      title: 'Thời gian gửi',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      render: (date: string) => (
        <span className="text-xs text-gray-500">
          {dayjs(date).format('DD/MM/YYYY HH:mm')}
        </span>
      ),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_: unknown, record: EvaluationResponse) => (
        <Tooltip title="Xem chi tiết các tiêu chí và nhận xét">
          <Button
            type="primary"
            ghost
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedEval(record);
              setIsDetailOpen(true);
            }}
            className="text-xs"
          >
            Chi tiết
          </Button>
        </Tooltip>
      ),
    },
  ];

  return (
    <>
      <Card
        title={
          <div className="flex items-center justify-between py-1">
            <span className="text-sm font-semibold flex items-center gap-2">
              <TeamOutlined style={{ color: '#1890ff' }} />
              Danh sách Học viên đã Đánh giá ({traineeEvaluations.length})
            </span>
            <Tag color="blue" className="text-xs py-0.5 px-2">
              <CheckCircleOutlined className="mr-1" /> {traineeEvaluations.length} lượt đánh giá
            </Tag>
          </div>
        }
        size="small"
        className="shadow-sm border-gray-100 rounded-xl overflow-hidden"
      >
        <Table
          columns={columns}
          dataSource={traineeEvaluations}
          rowKey="id"
          pagination={traineeEvaluations.length > 10 ? { pageSize: 10, size: 'small' } : false}
          size="middle"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Chưa có học viên nào gửi đánh giá cho buổi học này"
                style={{ margin: '16px 0' }}
              />
            ),
          }}
        />
      </Card>

      <EvaluationDetailModal
        open={isDetailOpen}
        evaluation={selectedEval}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedEval(null);
        }}
      />
    </>
  );
};
