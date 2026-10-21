import React from 'react';
import { Icon } from 'zmp-ui';
import { useNavigate } from 'react-router-dom';
import { navigateBack, navigateForward } from '@/utils/navigation';
import { PATHS } from '@/constants/paths';
import logoImg from '@/assets/logo.png';

export type HeaderProps =
  | {
    variant: 'logo';
    title?: string;
    showBack?: boolean;
    unreadCount?: number;
  }
  | {
    variant?: 'back' | 'title';
    title: string;
    showBack?: boolean;
    unreadCount?: number;
  };

const Header: React.FC<HeaderProps> = (props) => {
  const navigate = useNavigate();

  if (props.variant === 'logo') {
    const unreadCount = props.unreadCount ?? 0;
    return (
      <div className="z-10 bg-white">
        <div className="flex items-center justify-between h-12 px-3">
          <div className="flex items-center gap-1.5 min-w-0">
            <img src={logoImg} alt="" className="w-7 h-7 rounded-[26px] object-cover shrink-0" />
            <span className="font-semibold text-title-lg text-primary truncate">
              Hệ thống quản lý sinh hoạt DUT AI
            </span>
          </div>

          {/* Quick Notification Bell */}
          <button
            type="button"
            onClick={() => navigateForward(navigate, PATHS.NOTIFICATIONS)}
            className="relative w-8 h-8 rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-100 active:scale-95 transition-all shrink-0 ml-1"
          >
            <Icon icon="zi-notif" size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 bg-rose-500 text-white text-[8px] font-bold rounded-full min-w-3.5 h-3.5 px-0.5 flex items-center justify-center border border-white">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>
        </div>
        <div className="h-px bg-divider" />
      </div>
    );
  }

  const showBackButton = props.showBack ?? (props.variant === 'back');

  return (
    <div className="z-10 bg-white">
      <div className="flex items-center gap-2 h-11 px-2">
        {showBackButton && (
          <div
            className="flex items-center justify-center w-10 h-10 cursor-pointer text-primary"
            onClick={() => navigateBack(navigate)}
          >
            <Icon icon="zi-arrow-left" size={24} />
          </div>
        )}
        <span className={`font-medium text-title-lg text-primary ${!showBackButton ? 'px-2' : ''}`}>
          {props.title}
        </span>
      </div>
      <div className="h-px bg-divider" />
    </div>
  );
};

export default Header;
