import React from 'react';
import { RequestCategory } from '@/types/permission.types';

export interface CategoryFilterItem {
  key: string;
  label: string;
}

export const CATEGORIES_FILTER: CategoryFilterItem[] = [
  { key: 'ALL', label: 'Tất cả đơn' },
  { key: RequestCategory.CHANGE_MEETING, label: 'Đổi sinh hoạt' },
  { key: RequestCategory.ABSENCE, label: 'Vắng sinh hoạt' },
  { key: RequestCategory.LATE, label: 'Đi trễ' },
  { key: RequestCategory.POSTPONE, label: 'Hoãn bài tập' },
  { key: RequestCategory.OTHER, label: 'Khác' },
];

interface PermissionFiltersProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  filterMine: boolean;
  onToggleMine: (onlyMine: boolean) => void;
  canViewAll: boolean;
}

export const PermissionFilters: React.FC<PermissionFiltersProps> = ({
  selectedCategory,
  onSelectCategory,
  filterMine,
  onToggleMine,
  canViewAll,
}) => {
  return (
    <div className="flex flex-col gap-2.5">
      {/* 1. Mine vs All Switcher (if user has permission to see all) */}
      {canViewAll && (
        <div className="flex bg-gray-100 p-1 rounded-xl">
          <button
            onClick={() => onToggleMine(false)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
              !filterMine
                ? 'bg-white text-blue-600 shadow-xs'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Tất cả đơn hệ thống
          </button>
          <button
            onClick={() => onToggleMine(true)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filterMine
                ? 'bg-white text-blue-600 shadow-xs'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Đơn của tôi
          </button>
        </div>
      )}

      {/* 2. Horizontal Category Filter Chips */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
        {CATEGORIES_FILTER.map((item) => (
          <button
            key={item.key}
            onClick={() => onSelectCategory(item.key)}
            className={`px-3 py-1.5 rounded-xl font-medium shrink-0 transition-all ${
              selectedCategory === item.key
                ? 'bg-blue-600 text-white shadow-xs font-bold'
                : 'bg-white text-gray-600 border border-gray-200'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
