export const ExpenseStatus = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
} as const;

export type ExpenseStatusType = keyof typeof ExpenseStatus;

export interface ExpenseSpender {
  id: number;
  name: string;
  email: string;
}

export interface ExpenseTeam {
  id: number;
  team_name: string;
}

export interface ExpenseInvoice {
  id: string; // UUID
  expense_date: string; // YYYY-MM-DD
  amount: number;
  description: string;
  spender_id: number;
  team_id: number;
  status: ExpenseStatusType;
  payment_date: string | null;
  note: string | null;
  created_at: string;
  updated_at: string;
  spender?: ExpenseSpender;
  team?: ExpenseTeam;
}

export interface CreateExpenseDto {
  expense_date: string;
  amount: number;
  description: string;
  spender_id: number;
  team_id: number;
  status: ExpenseStatusType;
  payment_date?: string | null;
  note?: string | null;
}

export interface UpdateExpenseDto {
  expense_date?: string;
  amount?: number;
  description?: string;
  spender_id?: number;
  team_id?: number;
  status?: ExpenseStatusType;
  payment_date?: string | null;
  note?: string | null;
}

export interface ExpenseSummary {
  total_paid: number;
  total_unpaid: number;
  total: number;
}
