#!/usr/bin/env node
/**
 * Write public/data/latest.json and latest.csv from src/data/centres.json
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, 'src/data/centres.json');
const outDir = join(root, 'public/data');

const data = JSON.parse(readFileSync(src, 'utf8'));
mkdirSync(outDir, { recursive: true });

writeFileSync(join(outDir, 'latest.json'), JSON.stringify(data, null, 2) + '\n');

function csvEscape(v) {
  if (v == null) return '';
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

const julyPeriods = (data.meta.julyPeriods || data.meta.periods?.filter((p) => p.period.endsWith('-07')) || []).map(
  (p) => p.period,
);

const metricKeys = ['passRate', 'waitWeeks', 'delivered', 'noShow', 'abandoned'];

const headers = [
  'slug',
  'name',
  'county',
  'csoName',
  ...metricKeys,
  'period',
  'driveflowUrl',
  ...julyPeriods.flatMap((p) => {
    const key = p.replace('-', '_');
    return metricKeys.map((m) => `${m}_${key}`);
  }),
];

const rows = data.centres.map((c) => {
  const byPeriod = Object.fromEntries((c.history || []).map((h) => [h.period, h]));
  return [
    c.slug,
    c.name,
    c.county,
    c.csoName,
    ...metricKeys.map((m) => c[m] ?? ''),
    data.meta.period,
    c.driveflowUrl,
    ...julyPeriods.flatMap((p) => {
      const h = byPeriod[p] || {};
      return metricKeys.map((m) => h[m] ?? '');
    }),
  ]
    .map(csvEscape)
    .join(',');
});

const csv =
  [
    `# ${data.meta.citationLong || data.meta.citation}`,
    `# lastUpdated=${data.meta.lastUpdated}`,
    `# fullHistoryInJson=${data.meta.periods?.length ?? 0} months`,
    headers.join(','),
    ...rows,
  ].join('\n') + '\n';

writeFileSync(join(outDir, 'latest.csv'), csv);
console.log(
  `Wrote ${data.centres.length} centres to public/data/latest.{json,csv} (${data.meta.periods?.length ?? 0} months in JSON)`,
);
