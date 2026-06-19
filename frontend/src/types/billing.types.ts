export const InvoiceStatus = {
  PENDING: 'PENDING',
  PAID: 'PAID',
  CANCELLED: 'CANCELLED',
  EXPIRED: 'EXPIRED',
} as const;

export type InvoiceStatusType = keyof typeof InvoiceStatus;

export const InvoiceItemType = {
  VIOLATION: 'VIOLATION',
  FUND: 'FUND',
  DINING: 'DINING',
  OTHER: 'OTHER',
} as const;

export type InvoiceItemTypeType = keyof typeof InvoiceItemType;

export interface InvoiceItem {
  id: number;
  item_type: InvoiceItemTypeType;
  reference_id: number | null;
  amount: number;
  note: string | null;
}

export interface Invoice {
  id: number;
  user_id: number;
  amount: number;
  status: InvoiceStatusType;
  description: string;
  reference_code: string;
  payment_method: string;
  transaction_id: string | null;
  billing_period: string;
  created_at: string;
  updated_at: string;
  items: InvoiceItem[];
  qr_url: string;
}

export interface InvoiceCreateItem {
  item_type: InvoiceItemTypeType;
  reference_id?: number;
  amount?: number;
  note?: string;
}

export interface InvoiceCreate {
  user_id: number;
  items: InvoiceCreateItem[];
  billing_period: string;
  description?: string;
}

export interface MonthlyInvoiceItemPreview {
  user_id: number;
  user_name: string;
  violation_count: number;
  violation_amount: number;
  fund_amount: number;
  total_amount: number;
  description: string;
}

export interface MonthlyInvoicePreviewResponse {
  month: number;
  year: number;
  items: MonthlyInvoiceItemPreview[];
}

export interface MonthlyInvoiceCreate {
  month: number;
  year: number;
  team_id?: number | null;
  user_ids: number[];
  violation_price: number;
  fund_amount: number;
  extra_items: InvoiceCreateItem[];
  execute: boolean;
}
