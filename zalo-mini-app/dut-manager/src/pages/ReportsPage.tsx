import React from 'react';
import { Page, Box, Text, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useNavigate } from 'react-router-dom';
import { navigateForward } from '@/utils/navigation';
import { PATHS } from '@/constants/paths';

interface ReportSection {
  id: string;
  title: string;
  desc: string;
  icon: string;
  iconBg: string;
  badge?: string;
  badgeColor?: string;
  path: string;
}

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();

  const reportSections: ReportSection[] = [
    {
      id: 'academic',
      title: 'Báo cáo Học tập',
      desc: 'Nộp báo cáo đồ án, điểm số và tiến độ học tập',
      icon: 'zi-file-text',
      iconBg: 'bg-blue-50 text-blue-600',
      badge: 'Đến hạn',
      badgeColor: 'bg-amber-100 text-amber-800',
      path: PATHS.ACADEMIC_REPORTS,
    },
    {
      id: 'activity',
      title: 'Báo cáo Hoạt động',
      desc: 'Báo cáo tham gia workshop, seminar, sự kiện',
      icon: 'zi-check-circle',
      iconBg: 'bg-emerald-50 text-emerald-600',
      path: PATHS.ACTIVITY_REPORTS,
    },
    {
      id: 'homework',
      title: 'Bài tập về nhà',
      desc: 'Danh sách bài tập và nộp bài theo nhóm/cá nhân',
      icon: 'zi-note',
      iconBg: 'bg-indigo-50 text-indigo-600',
      badge: '2 bài tập',
      badgeColor: 'bg-blue-100 text-blue-800',
      path: PATHS.HOMEWORKS,
    },
    {
      id: 'permission',
      title: 'Đơn xin phép',
      desc: 'Gửi đơn xin nghỉ phép, vắng mặt hoạt động/họp',
      icon: 'zi-calendar',
      iconBg: 'bg-rose-50 text-rose-600',
      path: PATHS.PERMISSIONS,
    },
    {
      id: 'violation',
      title: 'Ghi nhận Vi phạm',
      desc: 'Theo dõi điểm trừ và lịch sử vi phạm quy chế lab',
      icon: 'zi-warning',
      iconBg: 'bg-orange-50 text-orange-600',
      path: PATHS.VIOLATIONS,
    },
  ];

  return (
    <Page className="bg-surface flex flex-col min-h-screen">
      <Header title="Báo cáo & Nhiệm vụ" showBack={false} />

      <div className="px-4 py-3 flex-1 flex flex-col gap-4 pb-24">
        {/* Banner Tổng kết */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 text-white shadow-md">
          <p className="text-xs uppercase font-bold tracking-wider opacity-80">Nhiệm vụ tuần này</p>
          <h3 className="text-lg font-bold mt-1">Hoàn thành báo cáo đúng hạn</h3>
          <p className="text-xs mt-1 opacity-90">Hạn chót nộp báo cáo học tập tuần là 23:59 Chủ Nhật.</p>
        </div>

        {/* List of Report Sections */}
        <div className="flex flex-col gap-3">
          <Text className="font-bold text-base text-gray-800">Danh mục Quản lý</Text>

          {reportSections.map((item) => (
            <div
              key={item.id}
              onClick={() => navigateForward(navigate, item.path)}
              className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-center justify-between cursor-pointer active:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-2xl ${item.iconBg} flex items-center justify-center`}>
                  <Icon icon={item.icon as any} size={24} />
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900 text-sm">{item.title}</span>
                    {item.badge && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.desc}</span>
                </div>
              </div>
              <Icon icon="zi-chevron-right" size={20} className="text-gray-400" />
            </div>
          ))}
        </div>
      </div>
    </Page>
  );
};

export default ReportsPage;
