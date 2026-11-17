import type { Schema } from '@/types/api';

export const InvoiceItemType = {
  VIOLATION: 'VIOLATION',
  FUND: 'FUND',
  DINING: 'DINING',
  OTHER: 'OTHER',
} as const;
export type InvoiceItemType = Schema<'InvoiceItemType'>;

export const InvoiceStatus = {
  PENDING: 'PENDING',
  PAID: 'PAID',
  CANCELLED: 'CANCELLED',
  EXPIRED: 'EXPIRED',
} as const;
export type InvoiceStatus = Schema<'InvoiceStatus'>;

export const FundCode = {
  DUT_AI: 'DUT_AI',
  DUT_MAKER: 'DUT_MAKER',
} as const;
export type FundCode = (typeof FundCode)[keyof typeof FundCode];

// OpenAPI Generated Schemas
export type InvoiceItem = Schema<'InvoiceItemResponse'>;
export type Invoice = Schema<'InvoiceResponse'> & {
  // Client-compatible optional fields for UI components
  fund_code?: string;
  user_name?: string | null;
  team_name?: string | null;
  total_amount?: number;
  invoice_code?: string;
};

export type InvoiceCreate = Omit<Schema<'InvoiceCreate'>, 'team_id'> & {
  fund_code?: string;
  team_id?: number | null;
};
export type InvoiceUpdate = Omit<Schema<'InvoiceUpdate'>, 'team_id'> & {
  fund_code?: string;
  team_id?: number | null;
};
export type InvoiceStatusUpdate = Schema<'InvoiceStatusUpdate'>;
export type MonthlyInvoiceCreate = Omit<Schema<'MonthlyInvoiceCreate'>, 'team_id'> & {
  fund_code?: string;
  team_id?: number | null;
};
export type MonthlyInvoiceItemPreview = Schema<'MonthlyInvoiceItemPreview'> & {
  extra_items_amount?: number;
  items?: InvoiceItem[];
};
export type MonthlyInvoicePreviewResponse = Schema<'MonthlyInvoicePreviewResponse'> & {
  total_users?: number;
  total_amount?: number;
};

// Form Values
export interface CreateInvoiceFormValues {
  user_ids: number[];
  user_id?: number;
  fund_code?: string;
  team_id?: number | null;
  billing_period: string;
  description?: string | null;
  items: Array<{
    item_type: InvoiceItemType;
    amount: number;
    note?: string | null;
    reference_id?: number | null;
  }>;
}

export interface UpdateInvoiceFormValues {
  fund_code?: string;
  team_id?: number | null;
  status?: InvoiceStatus;
  description?: string | null;
  items?: Array<{
    item_type: InvoiceItemType;
    amount: number;
    note?: string | null;
    reference_id?: number | null;
  }>;
}

export type InvoiceStatusType = InvoiceStatus;

export interface BillingSummary {
  total_amount: number;
  paid_amount: number;
  unpaid_amount: number;
}
