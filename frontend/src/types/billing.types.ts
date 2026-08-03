import { z } from 'zod';

export const InvoiceItemType = {
  VIOLATION: 'VIOLATION',
  FUND: 'FUND',
  DINING: 'DINING',
  OTHER: 'OTHER',
} as const;
export type InvoiceItemType = (typeof InvoiceItemType)[keyof typeof InvoiceItemType];

// Item Schema & Type
export const invoiceItemSchema = z.object({
  id: z.number().optional(),
  invoice_id: z.number().optional(),
  item_type: z.enum(['VIOLATION', 'FUND', 'DINING', 'OTHER']).or(z.string()),
  amount: z.number(),
  note: z.string().nullable().optional(),
  reference_id: z.number().nullable().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});
export type InvoiceItem = z.infer<typeof invoiceItemSchema>;

export const InvoiceStatus = {
  PENDING: 'PENDING',
  PAID: 'PAID',
  CANCELLED: 'CANCELLED',
  EXPIRED: 'EXPIRED',
} as const;
export type InvoiceStatus = (typeof InvoiceStatus)[keyof typeof InvoiceStatus];

// Response Schema & Type
export const invoiceSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  user_name: z.string().nullable().optional(),
  team_id: z.number().nullable().optional(),
  team_name: z.string().nullable().optional(),
  amount: z.number().optional(),
  total_amount: z.number().optional(),
  status: z.enum(['PENDING', 'PAID', 'CANCELLED', 'EXPIRED']),
  reference_code: z.string().optional(),
  invoice_code: z.string().optional(),
  description: z.string().nullable().optional(),
  billing_period: z.string(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  qr_url: z.string().optional(),
  team: z.object({ id: z.number(), team_name: z.string() }).nullable().optional(),
  items: z.array(invoiceItemSchema).default([]),
});
export type Invoice = z.infer<typeof invoiceSchema>;

// Create Request Schema & Type
export const createInvoiceSchema = z.object({
  user_id: z.number().min(1, 'Vui lòng chọn người nhận hóa đơn'),
  team_id: z.number().min(1, 'Vui lòng chọn nhóm'),
  billing_period: z.string().min(1, 'Vui lòng chọn kỳ hóa đơn'),
  description: z.string().optional().nullable(),
  items: z.array(invoiceItemSchema).min(1, 'Hóa đơn phải có ít nhất 1 mục'),
});
export type CreateInvoiceFormValues = z.infer<typeof createInvoiceSchema>;

// Update Request Schema & Type
export const updateInvoiceSchema = z.object({
  status: z.enum(['PENDING', 'PAID', 'CANCELLED', 'EXPIRED']).optional(),
  items: z.array(invoiceItemSchema).optional(),
});
export type UpdateInvoiceFormValues = z.infer<typeof updateInvoiceSchema>;
