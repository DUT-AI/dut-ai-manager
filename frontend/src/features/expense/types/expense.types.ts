import type { Schema } from '@/types/api';

export const ExpenseStatus = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
} as const;

export type ExpenseStatusType = Schema<'ExpenseStatus'>;

export type ExpenseSpender = Schema<'ExpenseSpenderInfo'>;
export type ExpenseTeam = Schema<'ExpenseTeamInfo'>;
export type ExpenseInvoice = Schema<'ExpenseInvoiceResponse'>;
export type CreateExpenseDto = Schema<'ExpenseInvoiceCreate'>;
export type UpdateExpenseDto = Schema<'ExpenseInvoiceUpdate'>;
export type ExpenseInvoiceStatusUpdate = Schema<'ExpenseInvoiceStatusUpdate'>;
export type ExpenseSummary = Schema<'ExpenseSummaryResponse'>;

export type CreateExpenseFormValues = CreateExpenseDto;
export type UpdateExpenseFormValues = UpdateExpenseDto;
