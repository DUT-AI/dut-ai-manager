import React from 'react';
import { RequestCategory } from '@/types/permission.types';

export interface CategoryFilterItem {
  key: string;
  label: string;
}

export const CATEGORIES_FILTER: CategoryFilterItem[] = [
  { key: 'ALL', label: 'Tất cả' },
  { key: RequestCategory.ABSENCE, label: 'Vắng sinh hoạt' },
  { key: RequestCategory.LATE, label: 'Đi trễ' },
  { key: RequestCategory.POSTPONE, label: 'Hoãn bài tập' },
  { key: RequestCategory.OTHER, label: 'Khác' },
];

interface PermissionFiltersProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

export const PermissionFilters: React.FC<PermissionFiltersProps> = ({
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
      {CATEGORIES_FILTER.map((item) => (
        <button
          key={item.key}
          onClick={() => onSelectCategory(item.key)}
          className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
            selectedCategory === item.key
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white text-gray-600 border border-gray-200'
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
};
