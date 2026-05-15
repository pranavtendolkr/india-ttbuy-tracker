import { formatLong } from '@/lib/dates';
import type { LatestRate } from '@/lib/types';

type Props = {
  rows: LatestRate[];
  currency: string;
};

export function LatestRatesTable({ rows, currency }: Props) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
        No latest rates yet.
      </div>
    );
  }

  const sorted = [...rows].sort((a, b) => b.rate_value - a.rate_value);
  const best = sorted[0]?.rate_value ?? 0;

  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-800">
      <table className="min-w-full divide-y divide-neutral-200 text-sm dark:divide-neutral-800">
        <thead className="bg-neutral-100 dark:bg-neutral-900">
          <tr>
            <Th>Bank</Th>
            <Th align="right">Latest {currency} TT-Buy</Th>
            <Th>Effective</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
          {sorted.map((row) => {
            const isBest = row.rate_value === best;
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
                    {row.rate_value.toFixed(4)}
                  </span>
                </Td>
                <Td>
                  <span className="text-neutral-600 dark:text-neutral-400">
                    {formatLong(row.effective_date)}
                  </span>
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
