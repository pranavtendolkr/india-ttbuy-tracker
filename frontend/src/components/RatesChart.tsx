'use client';

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { colorForBank } from '@/lib/colors';
import { formatShort, formatLong } from '@/lib/dates';
import type { Bank, Rate } from '@/lib/types';

type Props = {
  banks: Bank[];
  rates: Rate[];
  selectedBankIds: Set<string>;
};

type ChartRow = {
  date: string;
  [bankSlug: string]: string | number | null;
};

export function RatesChart({ banks, rates, selectedBankIds }: Props) {
  const visibleBanks = banks.filter((b) => selectedBankIds.has(b.id));
  const data = buildSeries(rates, visibleBanks);

  if (data.length === 0) {
    return (
      <div className="flex h-[360px] items-center justify-center rounded-lg border border-dashed border-neutral-300 text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
        No rate data in the selected window. Try a wider range.
      </div>
    );
  }

  return (
    <div className="h-[360px] w-full sm:h-[420px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
          <XAxis
            dataKey="date"
            tickFormatter={formatShort}
            minTickGap={32}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => v.toFixed(2)}
            width={64}
          />
          <Tooltip
            labelFormatter={(label: string) => formatLong(label)}
            formatter={(value: number | string) =>
              typeof value === 'number' ? value.toFixed(2) : value
            }
            contentStyle={{ fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {visibleBanks.map((bank, idx) => {
            const color = colorForBank(bank.slug, idx);
            // When the series has only a handful of points, lines aren't
            // visible. Force dots in that case so the user sees data.
            const points = data.reduce(
              (acc, row) => acc + (row[bank.slug] != null ? 1 : 0),
              0,
            );
            const showDots = points <= 5;
            return (
              <Line
                key={bank.id}
                type="monotone"
                dataKey={bank.slug}
                name={bank.name}
                stroke={color}
                dot={showDots ? { r: 3, fill: color } : false}
                strokeWidth={2}
                connectNulls={false}
                isAnimationActive={false}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function buildSeries(rates: Rate[], banks: Bank[]): ChartRow[] {
  const slugById = new Map(banks.map((b) => [b.id, b.slug]));
  const dates = new Set<string>();
  for (const r of rates) {
    if (slugById.has(r.bank_id)) dates.add(r.effective_date);
  }
  const sortedDates = Array.from(dates).sort();
  const rowsByDate = new Map<string, ChartRow>();
  for (const date of sortedDates) {
    const row: ChartRow = { date };
    for (const bank of banks) row[bank.slug] = null;
    rowsByDate.set(date, row);
  }
  for (const r of rates) {
    const slug = slugById.get(r.bank_id);
    if (!slug) continue;
    const row = rowsByDate.get(r.effective_date);
    if (row) row[slug] = r.rate_value;
  }
  return sortedDates.map((d) => rowsByDate.get(d) as ChartRow);
}
