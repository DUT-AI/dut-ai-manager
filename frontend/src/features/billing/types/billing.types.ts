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

// OpenAPI Generated Schemas
export type InvoiceItem = Schema<'InvoiceItemResponse'>;
export type Invoice = Schema<'InvoiceResponse'> & {
  // Client-compatible optional fields for UI components
  user_name?: string | null;
  team_name?: string | null;
  total_amount?: number;
  invoice_code?: string;
};

export type InvoiceCreate = Schema<'InvoiceCreate'>;
export type InvoiceUpdate = Schema<'InvoiceUpdate'>;
export type InvoiceStatusUpdate = Schema<'InvoiceStatusUpdate'>;
export type MonthlyInvoiceCreate = Schema<'MonthlyInvoiceCreate'>;
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
  team_id: number;
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
