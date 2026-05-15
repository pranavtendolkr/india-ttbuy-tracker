export type Bank = {
  id: string;
  name: string;
  slug: string;
  source_url: string;
  parser_type: 'html' | 'pdf' | 'html_dynamic';
  enabled: boolean;
};

export type Rate = {
  id: number;
  bank_id: string;
  currency: string;
  rate_type: string;
  rate_value: number;
  effective_date: string; // ISO date (YYYY-MM-DD)
  scraped_at: string;
  source_url: string | null;
  source_title: string | null;
  parser_version: string | null;
  source_status: string | null;
  notes: string | null;
};

export type LatestRate = Rate & {
  bank_slug: string;
  bank_name: string;
};
