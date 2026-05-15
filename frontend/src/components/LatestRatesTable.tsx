import { formatLong } from '@/lib/dates';
import type { Bank, LatestRate } from '@/lib/types';

type Props = {
  rows: LatestRate[];
  currency: string;
  /** When set, the table is in "as of" mode and stale rates get a badge.
   *  When undefined, the heading reads "Latest". */
  asOf?: string;
  /** All enabled banks; needed so we can show a row for banks that had
   *  not published yet by the picked date. */
  allBanks?: Bank[];
};

export function LatestRatesTable({ rows, currency, asOf, allBanks }: Props) {
  const rowsByBankId = new Map(rows.map((r) => [r.bank_id, r]));
  const completeRows: Array<LatestRate | { bank_id: string; bank_name: string }> =
    allBanks && allBanks.length > 0
      ? allBanks.map((b) => rowsByBankId.get(b.id) ?? { bank_id: b.id, bank_name: b.name })
      : rows;

  if (completeRows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
        No rates available.
      </div>
    );
  }

  const populated = completeRows.filter(
    (r): r is LatestRate => 'rate_value' in r,
  );
  const sorted = [...completeRows].sort((a, b) => {
    const av = 'rate_value' in a ? a.rate_value : -Infinity;
    const bv = 'rate_value' in b ? b.rate_value : -Infinity;
    return bv - av;
  });
  const best = populated.length > 0 ? Math.max(...populated.map((r) => r.rate_value)) : 0;

  const dateLabel = asOf ? `${currency} TT-Buy (as of ${formatLong(asOf)})` : `Latest ${currency} TT-Buy`;

  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-800">
      <table className="min-w-full divide-y divide-neutral-200 text-sm dark:divide-neutral-800">
        <thead className="bg-neutral-100 dark:bg-neutral-900">
          <tr>
            <Th>Bank</Th>
            <Th align="right">{dateLabel}</Th>
            <Th>Effective date</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
          {sorted.map((row) => {
            if (!('rate_value' in row)) {
              return (
                <tr key={row.bank_id}>
                  <Td><span className="font-medium">{row.bank_name}</span></Td>
                  <Td align="right">
                    <span className="text-neutral-400">-</span>
                  </Td>
                  <Td>
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">
                      no data on or before this date
                    </span>
                  </Td>
                  <Td><span className="text-neutral-400">-</span></Td>
                </tr>
              );
            }
            const isBest = populated.length > 1 && row.rate_value === best;
            const staleness = stalenessLabel(row.effective_date, asOf);
            return (
              <tr key={`${row.bank_id}-${row.effective_date}`}>
                <Td>
                  <span className="font-medium">{row.bank_name}</span>
                </Td>
                <Td align="right">
                  <span
                    className={
                      isBest
                        ? 'font-semibold text-emerald-700 dark:text-emerald-400'
                        : 'tabular-nums'
                    }
                  >
                    {row.rate_value.toFixed(2)}
                  </span>
                </Td>
                <Td>
                  <div className="flex items-center gap-2">
                    <span className="text-neutral-600 dark:text-neutral-400">
                      {formatLong(row.effective_date)}
                    </span>
                    {staleness && (
                      <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                        {staleness}
                      </span>
                    )}
                  </div>
                </Td>
                <Td>
                  {row.source_url ? (
                    <a
                      className="text-blue-600 underline-offset-2 hover:underline dark:text-blue-400"
                      href={row.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      view
                    </a>
                  ) : (
                    <span className="text-neutral-400">-</span>
                  )}
                </Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function stalenessLabel(effective: string, asOf?: string): string | null {
  if (!asOf) return null;
  if (effective === asOf) return null;
  const days = daysBetween(effective, asOf);
  if (days <= 0) return null;
  if (days === 1) return 'from 1 day earlier';
  return `from ${days} days earlier`;
}

function daysBetween(fromIso: string, toIso: string): number {
  const [y1, m1, d1] = fromIso.split('-').map(Number);
  const [y2, m2, d2] = toIso.split('-').map(Number);
  const a = Date.UTC(y1, m1 - 1, d1);
  const b = Date.UTC(y2, m2 - 1, d2);
  return Math.round((b - a) / (1000 * 60 * 60 * 24));
}

function Th({
  children,
  align = 'left',
}: {
  children: React.ReactNode;
  align?: 'left' | 'right';
}) {
  return (
    <th
      scope="col"
      className={`px-3 py-2 text-${align} text-xs font-semibold uppercase tracking-wide text-neutral-600 dark:text-neutral-400`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  align = 'left',
}: {
  children: React.ReactNode;
  align?: 'left' | 'right';
}) {
  return <td className={`whitespace-nowrap px-3 py-2 text-${align}`}>{children}</td>;
}
