import React from 'react';
import { Page, Icon, useSnackbar } from 'zmp-ui';
import { configAppView, showOAWidget } from 'zmp-sdk';
import { useNavigate } from 'react-router-dom';
import { navigateForward } from '@/utils/navigation';
import { PATHS } from '@/constants/paths';
import iconTatCa from '@/assets/icons/icon-apps.png';
import utilLichHoc from '@/assets/icons/icon-calendar.png';
import utilGiaoTrinh from '@/assets/icons/icon-school-board.png';
import utilLichThi from '@/assets/icons/icon-shopping-list.png';
import utilTaiLieu from '@/assets/icons/icon-book-open.png';
import utilCuocThi from '@/assets/icons/icon-medal.png';

interface Utility {
  id: number;
  title: string;
  icon: string;
  path?: string;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { openSnackbar } = useSnackbar();
  const showComingSoon = (): void => {
    openSnackbar({ text: 'Chức năng đang được phát triển.', type: 'info', duration: 1500 });
  };
  const [utilitiesExpanded, setUtilitiesExpanded] = React.useState<boolean>(true);

  React.useEffect(() => {
    configAppView({
      headerColor: '#ffffff',
      headerTextColor: 'black',
      actionBar: { hide: true },
    }).catch(() => { });
  }, []);

  React.useEffect(() => {
    showOAWidget({
      id: 'oaWidget',
      guidingText: 'Quan tâm OA để nhận các chương trình đặc quyền ưu đãi',
      color: '#0068FF',
      paddingTop: '12px',
      paddingBottom: '12px',
      paddingLeft: '16px',
      paddingRight: '16px',
      fontFamily: 'Roboto',
      fontSize: '15px',
      lineHeight: '20px',
    });
  }, []);

  const utilities: Utility[] = [
    { id: 1, title: 'Bài tập', icon: utilGiaoTrinh, path: PATHS.HOMEWORKS },
    { id: 2, title: 'Đơn phép', icon: utilLichThi, path: PATHS.PERMISSIONS },
    { id: 3, title: 'Lịch họp', icon: utilLichHoc, path: PATHS.MEETINGS },
    { id: 4, title: 'Vi phạm', icon: utilCuocThi, path: PATHS.VIOLATIONS },
    { id: 5, title: 'Hóa đơn', icon: utilTaiLieu, path: PATHS.INVOICES },
    { id: 6, title: 'Tất cả', icon: iconTatCa, path: PATHS.SHORTCUTS },
  ];

  return (
    <Page className="bg-surface">
      {/* Content */}
      <div className="px-4 pt-3 pb-20 flex flex-col gap-3">
        {/* Search Bar */}
        <div className="flex flex-row items-center py-2 pl-4 pr-2 gap-2 bg-white rounded-[30px]">
          <Icon icon="zi-search" size={24} style={{ color: '#a9adb2', flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Tìm tính năng, bài tập, đơn phép, lịch..."
            className="flex-1 border-none outline-none bg-transparent text-body-lg text-primary p-0 placeholder:text-icon"
          />
        </div>

        {/* Tiện ích (Unified Grid as requested) */}
        <div
          className={`bg-white rounded-2xl border border-gray-100 shadow-xs flex flex-col items-center ${utilitiesExpanded ? 'pb-4' : ''
            }`}
        >
          <div
            onClick={() => setUtilitiesExpanded(!utilitiesExpanded)}
            className="flex flex-row items-center justify-between px-4 py-3.5 w-full cursor-pointer"
          >
            <span className="text-title-md font-semibold text-primary leading-5.5">Tiện ích</span>
            <Icon
              icon={utilitiesExpanded ? 'zi-chevron-up' : 'zi-chevron-down'}
              size={18}
              style={{ color: '#888' }}
            />
          </div>

          {utilitiesExpanded && (
            <div className="grid grid-cols-4 gap-y-4 gap-x-2 px-2 w-full">
              {utilities.map((util) => (
                <div
                  key={util.id}
                  onClick={() => {
                    if (util.path) {
                      navigateForward(navigate, util.path);
                    } else {
                      showComingSoon();
                    }
                  }}
                  className="flex flex-col items-center gap-1.5 cursor-pointer active:scale-95 transition-transform"
                >
                  <div className="w-13 h-13 rounded-2xl bg-icon-bg flex items-center justify-center">
                    <img src={util.icon} alt={util.title} className="w-7 h-7 object-contain" />
                  </div>
                  <span className="text-body-sm text-primary text-center leading-4 font-normal">
                    {util.title}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Page>
  );
};

export default HomePage;
