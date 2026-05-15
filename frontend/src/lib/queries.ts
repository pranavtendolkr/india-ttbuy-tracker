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

/**
 * Returns one row per enabled bank: the most recent rate published on or
 * before ``asOf``. Banks that have not published anything by ``asOf`` are
 * omitted (not returned at all). The frontend can compare each row's
 * effective_date against ``asOf`` to decide whether to render a "stale"
 * badge.
 *
 * Implemented client-side rather than via a SQL view so we don't need an
 * extra migration. With ~11 banks and modest history the payload stays
 * tiny.
 */
export async function getRatesAsOf(
  currency: string,
  asOf: string,
  rateType = 'inward_tt_buy',
): Promise<LatestRate[]> {
  const supabase = getSupabase();
  const { data: banks, error: banksErr } = await supabase
    .from('banks')
    .select('id, name, slug')
    .eq('enabled', true);
  if (banksErr) throw banksErr;

  const { data: rates, error: ratesErr } = await supabase
    .from('rates')
    .select(
      'bank_id, currency, rate_type, rate_value, effective_date, scraped_at, source_url, source_title, parser_version, source_status, notes, id',
    )
    .eq('currency', currency)
    .eq('rate_type', rateType)
    .lte('effective_date', asOf)
    .order('effective_date', { ascending: false })
    .order('scraped_at', { ascending: false });
  if (ratesErr) throw ratesErr;

  const bankById = new Map(
    (banks ?? []).map((b) => [b.id as string, b as { id: string; name: string; slug: string }]),
  );
  const seen = new Set<string>();
  const out: LatestRate[] = [];
  for (const r of rates ?? []) {
    if (seen.has(r.bank_id as string)) continue;
    const bank = bankById.get(r.bank_id as string);
    if (!bank) continue; // disabled bank
    seen.add(r.bank_id as string);
    out.push({
      ...(r as Rate),
      bank_slug: bank.slug,
      bank_name: bank.name,
    });
  }
  out.sort((a, b) => a.bank_name.localeCompare(b.bank_name));
  return out;
}
