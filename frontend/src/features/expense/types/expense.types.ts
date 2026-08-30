import { z } from 'zod';

export const ExpenseStatus = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
} as const;

export type ExpenseStatusType = (typeof ExpenseStatus)[keyof typeof ExpenseStatus];
export const expenseStatusSchema = z.enum(['UNPAID', 'PAID']);

export const expenseSpenderSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
});
export type ExpenseSpender = z.infer<typeof expenseSpenderSchema>;

export const expenseTeamSchema = z.object({
  id: z.number(),
  team_name: z.string(),
});
export type ExpenseTeam = z.infer<typeof expenseTeamSchema>;

export const expenseInvoiceSchema = z.object({
  id: z.string(),
  expense_date: z.string(),
  amount: z.number(),
  description: z.string(),
  spender_id: z.number(),
  team_id: z.number(),
  status: expenseStatusSchema,
  payment_date: z.string().nullable().optional(),
  note: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  spender: expenseSpenderSchema.optional(),
  team: expenseTeamSchema.optional(),
});
export type ExpenseInvoice = z.infer<typeof expenseInvoiceSchema>;

export const createExpenseDtoSchema = z.object({
  expense_date: z.string().min(1, 'Vui lòng chọn ngày hóa đơn'),
  amount: z.number().min(0, 'Số tiền phải lớn hơn hoặc bằng 0'),
  description: z.string().min(1, 'Vui lòng nhập mô tả'),
  spender_id: z.number().min(1, 'Vui lòng chọn người chi'),
  team_id: z.number().min(1, 'Vui lòng chọn nhóm'),
  status: expenseStatusSchema,
  payment_date: z.string().nullable().optional(),
  note: z.string().nullable().optional(),
});
export type CreateExpenseDto = z.infer<typeof createExpenseDtoSchema>;
export type CreateExpenseFormValues = CreateExpenseDto;

export const updateExpenseDtoSchema = createExpenseDtoSchema.partial();
export type UpdateExpenseDto = z.infer<typeof updateExpenseDtoSchema>;
export type UpdateExpenseFormValues = UpdateExpenseDto;

export const expenseSummarySchema = z.object({
  total_paid: z.number(),
  total_unpaid: z.number(),
  total: z.number(),
});
export type ExpenseSummary = z.infer<typeof expenseSummarySchema>;
