import { getSupabase } from './supabase';
import type { Bank, LatestRate, Rate } from './types';

export async function getBanks(): Promise<Bank[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('banks')
    .select('id, name, slug, source_url, parser_type, enabled')
    .eq('enabled', true)
    .order('name');
  if (error) throw error;
  return (data ?? []) as Bank[];
}

export type GetRatesArgs = {
  currency: string;
  rateType?: string;
  from?: string; // ISO date
  to?: string;   // ISO date
  bankIds?: string[];
};

export async function getRates({
  currency,
  rateType = 'inward_tt_buy',
  from,
  to,
  bankIds,
}: GetRatesArgs): Promise<Rate[]> {
  const supabase = getSupabase();
  let query = supabase
    .from('rates')
    .select(
      'id, bank_id, currency, rate_type, rate_value, effective_date, scraped_at, source_url, source_title, parser_version, source_status, notes',
    )
    .eq('currency', currency)
    .eq('rate_type', rateType)
    .order('effective_date', { ascending: true });
  if (from) query = query.gte('effective_date', from);
  if (to) query = query.lte('effective_date', to);
  if (bankIds && bankIds.length > 0) query = query.in('bank_id', bankIds);
  const { data, error } = await query;
  if (error) throw error;
  return (data ?? []) as Rate[];
}

export async function getLatestPerBank(
  currency: string,
  rateType = 'inward_tt_buy',
): Promise<LatestRate[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('latest_rates')
    .select('*')
    .eq('currency', currency)
    .eq('rate_type', rateType)
    .order('bank_name');
  if (error) throw error;
  return (data ?? []) as LatestRate[];
}
