'use client';

import { useEffect, useMemo, useState } from 'react';

import { Controls } from './Controls';
import { LatestRatesTable } from './LatestRatesTable';
import { RatesChart } from './RatesChart';
import { daysAgoIso } from '@/lib/dates';
import { getBanks, getLatestPerBank, getRates } from '@/lib/queries';
import { SUPABASE_CONFIGURED } from '@/lib/supabase';
import type { Bank, LatestRate, Rate } from '@/lib/types';

const DEFAULT_RANGE_ID = '90';
const DEFAULT_RANGE_DAYS: number | null = 90;

export function Dashboard() {
  const [currency, setCurrency] = useState('USD');
  const [rangeId, setRangeId] = useState(DEFAULT_RANGE_ID);
  const [rangeDays, setRangeDays] = useState<number | null>(DEFAULT_RANGE_DAYS);
  const [banks, setBanks] = useState<Bank[]>([]);
  const [selectedBankIds, setSelectedBankIds] = useState<Set<string>>(new Set());
  const [rates, setRates] = useState<Rate[]>([]);
  const [latest, setLatest] = useState<LatestRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!SUPABASE_CONFIGURED) {
      setError('Supabase env vars are not configured. See README for setup.');
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const list = await getBanks();
        if (cancelled) return;
        setBanks(list);
        setSelectedBankIds(new Set(list.map((b) => b.id)));
      } catch (e) {
        if (!cancelled) setError(stringifyError(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!SUPABASE_CONFIGURED) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    const from = rangeDays != null ? daysAgoIso(rangeDays) : undefined;
    (async () => {
      try {
        const [series, latestRows] = await Promise.all([
          getRates({ currency, from }),
          getLatestPerBank(currency),
        ]);
        if (cancelled) return;
        setRates(series);
        setLatest(latestRows);
      } catch (e) {
        if (!cancelled) setError(stringifyError(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [currency, rangeDays]);

  const toggleBank = (id: string) => {
    setSelectedBankIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelectedBankIds(new Set(banks.map((b) => b.id)));
  const clearAll = () => setSelectedBankIds(new Set());

  const visibleLatest = useMemo(
    () => latest.filter((r) => selectedBankIds.has(r.bank_id)),
    [latest, selectedBankIds],
  );

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          India inward remittance TT-buy rates
        </h1>
        <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
          Daily snapshots of the rate banks apply when USD is wired in and converted to INR.
          Higher is better for the receiver. Missing days appear as gaps.
        </p>
      </header>

      <section className="mb-6 space-y-4 rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
        <Controls
          banks={banks}
          selectedBankIds={selectedBankIds}
          onToggleBank={toggleBank}
          onSelectAll={selectAll}
          onClearAll={clearAll}
          currency={currency}
          onCurrencyChange={setCurrency}
          rangeId={rangeId}
          onRangeChange={(id, days) => {
            setRangeId(id);
            setRangeDays(days);
          }}
        />
      </section>

      <section className="mb-8 rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
        {error ? (
          <ErrorBanner message={error} />
        ) : loading ? (
          <ChartSkeleton />
        ) : (
          <RatesChart banks={banks} rates={rates} selectedBankIds={selectedBankIds} />
        )}
      </section>

      <section className="mb-12">
        <h2 className="mb-3 text-lg font-semibold">Latest rate per bank</h2>
        <LatestRatesTable rows={visibleLatest} currency={currency} />
      </section>

      <footer className="border-t border-neutral-200 pt-4 text-xs text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
        Data scraped daily from each bank&rsquo;s public rate sheet. This site is informational
        only and not financial advice. Always confirm the applicable rate with your bank
        before initiating a transfer.
      </footer>
    </main>
  );
}

function ChartSkeleton() {
  return (
    <div className="h-[360px] w-full animate-pulse rounded-md bg-neutral-100 dark:bg-neutral-800 sm:h-[420px]" />
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
      {message}
    </div>
  );
}

function stringifyError(e: unknown): string {
  if (e instanceof Error) return e.message;
  try {
    return JSON.stringify(e);
  } catch {
    return String(e);
  }
}
