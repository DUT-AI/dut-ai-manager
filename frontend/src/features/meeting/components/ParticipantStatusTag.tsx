import React from 'react';
import { Tag } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { ParticipantStatus } from '../types/meeting.types';

interface Props {
  status?: ParticipantStatus | string;
  className?: string;
}

export const ParticipantStatusTag: React.FC<Props> = ({ status, className = 'px-2.5 py-0.5 text-xs font-medium' }) => {
  let tagColor = 'default';
  let tagIcon = <CloseCircleOutlined />;
  let tagText = 'Chưa checkin';

  switch (status) {
    case ParticipantStatus.JOINED:
      tagColor = 'green';
      tagIcon = <CheckCircleOutlined />;
      tagText = 'Đã checkin';
      break;
    case ParticipantStatus.LATE_EXCUSED:
      tagColor = 'blue';
      tagIcon = <ClockCircleOutlined />;
      tagText = 'Trễ (Có phép)';
      break;
    case ParticipantStatus.LATE_UNEXCUSED:
      tagColor = 'orange';
      tagIcon = <ClockCircleOutlined />;
      tagText = 'Trễ (Không phép)';
      break;
    case ParticipantStatus.ABSENT_EXCUSED:
      tagColor = 'purple';
      tagIcon = <CloseCircleOutlined />;
      tagText = 'Vắng (Có phép)';
      break;
    case ParticipantStatus.ABSENT_UNEXCUSED:
      tagColor = 'red';
      tagIcon = <CloseCircleOutlined />;
      tagText = 'Vắng (Không phép)';
      break;
    case ParticipantStatus.COMPLETED:
      tagColor = 'cyan';
      tagIcon = <CheckCircleOutlined />;
      tagText = 'Hoàn thành';
      break;
    case ParticipantStatus.NOT_JOINED:
    default:
      tagColor = 'default';
      tagIcon = <CloseCircleOutlined />;
      tagText = 'Chưa checkin';
      break;
  }

  return (
    <Tag color={tagColor} icon={tagIcon} className={className}>
      {tagText}
    </Tag>
  );
};
