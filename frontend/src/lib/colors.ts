// Stable, accessible color palette for line charts. Indexed by bank slug
// position; falls back to a hash-based pick for unknown slugs.
const PALETTE = [
  '#2563eb', // blue-600
  '#dc2626', // red-600
  '#059669', // emerald-600
  '#d97706', // amber-600
  '#7c3aed', // violet-600
  '#0891b2', // cyan-600
  '#db2777', // pink-600
  '#65a30d', // lime-600
  '#475569', // slate-600
];

export function colorForBank(slug: string, index: number): string {
  if (index >= 0 && index < PALETTE.length) return PALETTE[index];
  let h = 0;
  for (let i = 0; i < slug.length; i++) h = (h * 31 + slug.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}
