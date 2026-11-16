import type { Schema } from '@/types/api';

export const ExpenseStatus = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
} as const;

export type ExpenseStatusType = Schema<'ExpenseStatus'>;

export type ExpenseSpender = Schema<'ExpenseSpenderInfo'>;
export type ExpenseTeam = Schema<'ExpenseTeamInfo'>;
export type ExpenseInvoice = Schema<'ExpenseInvoiceResponse'> & {
  fund_code?: string;
};
export type CreateExpenseDto = Schema<'ExpenseInvoiceCreate'> & {
  fund_code?: string;
  team_id?: number | null;
};
export type UpdateExpenseDto = Schema<'ExpenseInvoiceUpdate'> & {
  fund_code?: string;
  team_id?: number | null;
};
export type ExpenseInvoiceStatusUpdate = Schema<'ExpenseInvoiceStatusUpdate'>;
export type ExpenseSummary = Schema<'ExpenseSummaryResponse'>;

export type CreateExpenseFormValues = CreateExpenseDto;
export type UpdateExpenseFormValues = UpdateExpenseDto;
