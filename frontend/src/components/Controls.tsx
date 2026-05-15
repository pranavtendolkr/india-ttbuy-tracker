'use client';

import { colorForBank } from '@/lib/colors';
import type { Bank } from '@/lib/types';

const RANGE_PRESETS = [
  { id: '30', label: '30D', days: 30 },
  { id: '90', label: '90D', days: 90 },
  { id: '365', label: '1Y', days: 365 },
  { id: 'all', label: 'All', days: null as number | null },
];

type Props = {
  banks: Bank[];
  selectedBankIds: Set<string>;
  onToggleBank: (id: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  currency: string;
  onCurrencyChange: (c: string) => void;
  rangeId: string;
  onRangeChange: (id: string, days: number | null) => void;
};

export function Controls({
  banks,
  selectedBankIds,
  onToggleBank,
  onSelectAll,
  onClearAll,
  currency,
  onCurrencyChange,
  rangeId,
  onRangeChange,
}: Props) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm">
          <span className="font-medium text-neutral-700 dark:text-neutral-300">Currency</span>
          <select
            value={currency}
            onChange={(e) => onCurrencyChange(e.target.value)}
            className="rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-900"
          >
            <option value="USD">USD</option>
          </select>
        </label>

        <div
          role="group"
          aria-label="Date range"
          className="inline-flex overflow-hidden rounded-md border border-neutral-300 dark:border-neutral-700"
        >
          {RANGE_PRESETS.map((preset) => {
            const active = preset.id === rangeId;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => onRangeChange(preset.id, preset.days)}
                className={
                  'px-3 py-1 text-sm transition-colors ' +
                  (active
                    ? 'bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900'
                    : 'bg-white text-neutral-700 hover:bg-neutral-100 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800')
                }
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Banks
          </span>
          <div className="space-x-2 text-xs">
            <button
              type="button"
              onClick={onSelectAll}
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              Select all
            </button>
            <button
              type="button"
              onClick={onClearAll}
              className="text-neutral-500 hover:underline dark:text-neutral-400"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {banks.map((bank, idx) => {
            const active = selectedBankIds.has(bank.id);
            const color = colorForBank(bank.slug, idx);
            return (
              <button
                key={bank.id}
                type="button"
                onClick={() => onToggleBank(bank.id)}
                aria-pressed={active}
                className={
                  'flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition-colors ' +
                  (active
                    ? 'border-neutral-900 bg-white text-neutral-900 dark:border-neutral-100 dark:bg-neutral-100 dark:text-neutral-900'
                    : 'border-neutral-300 bg-white text-neutral-500 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400')
                }
              >
                <span
                  aria-hidden
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ backgroundColor: color }}
                />
                {bank.name}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
