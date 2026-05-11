import { useEffect, useState } from 'react';
import { Tag, Tooltip } from 'antd';
import { TrophyOutlined, StarOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

interface UserTitleBadgeProps {
  userId: number;
  showIcon?: boolean;
}

const TITLE_CONFIG: Record<string, { color: string; icon: React.ReactNode; description: string }> = {
  'Tích cực': {
    color: 'gold',
    icon: <TrophyOutlined />,
    description: 'Hoạt động tích cực - điểm cao, vi phạm ít',
  },
  'Bình thường': {
    color: 'blue',
    icon: <StarOutlined />,
    description: 'Hoạt động bình thường',
  },
  'Hoạt động kém': {
    color: 'red',
    icon: <ExclamationCircleOutlined />,
    description: 'Hoạt động kém - vi phạm nhiều hoặc vắng mặt',
  },
};

export const UserTitleBadge = ({ userId, showIcon = true }: UserTitleBadgeProps) => {
  const [title, setTitle] = useState<string | null>(null);

  useEffect(() => {
    const fetchTitle = async () => {
      try {
        const response = await fetch(`/api/v1/reports/users/${userId}/current-title`);
        const result = await response.json();
        if (result.success) {
          setTitle(result.data);
        }
      } catch (error) {
        console.error('Failed to fetch title:', error);
      }
    };

    fetchTitle();
  }, [userId]);

  if (!title) return null;

  const config = TITLE_CONFIG[title] || {
    color: 'default',
    icon: null,
    description: 'Chưa có danh hiệu',
  };

  return (
    <Tooltip title={config.description}>
      <Tag
        color={config.color}
        icon={showIcon && config.icon}
      >
        {title}
      </Tag>
    </Tooltip>
  );
};

export const TitleBadge = ({ title }: { title: string }) => {
  const config = TITLE_CONFIG[title] || {
    color: 'default',
    icon: null,
    description: 'Chưa có danh hiệu',
  };

  return (
    <Tooltip title={config.description}>
      <Tag color={config.color} icon={config.icon}>
        {title}
      </Tag>
    </Tooltip>
  );
};
