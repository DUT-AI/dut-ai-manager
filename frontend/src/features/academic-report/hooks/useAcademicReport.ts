import { useQuery } from '@tanstack/react-query';
import { reportService } from '@/features/academic-report/services/report.service';

export interface AcademicReportFilter {
  type: 'bonus' | 'violation';
  month?: number;
  year?: number;
  startDate?: string;
  endDate?: string;
  keyword?: string;
  enabled?: boolean;
}

export const academicReportKeys = {
  all: ['academicReports'] as const,
  list: (filters: Omit<AcademicReportFilter, 'enabled'>) => ['academicReports', filters] as const,
};

export const useAcademicReport = (filters: AcademicReportFilter) => {
  const { enabled = true, type, month, year, startDate, endDate, keyword } = filters;

  return useQuery({
    queryKey: academicReportKeys.list({ type, month, year, startDate, endDate, keyword }),
    queryFn: async () => {
      if (type === 'bonus') {
        return await reportService.getBonusPointReport(month, year, keyword, startDate, endDate);
      }
      return await reportService.getViolationReport(month, year, keyword, startDate, endDate);
    },
    staleTime: 60 * 1000,
    enabled,
  });
};
