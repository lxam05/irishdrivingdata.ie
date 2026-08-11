import raw from '../data/centres.json';
import coordsRaw from '../data/centre-coords.json';

export type MetricKey = 'passRate' | 'waitWeeks' | 'delivered' | 'noShow' | 'abandoned';

export type HistoryPoint = {
  period: string;
  passRate: number | null;
  waitWeeks: number | null;
  delivered?: number | null;
  noShow?: number | null;
  abandoned?: number | null;
};

export type PeriodMeta = {
  period: string;
  label: string;
  metrics: string[];
};

export type Centre = {
  slug: string;
  name: string;
  county: string;
  csoName: string | null;
  passRate: number | null;
  waitWeeks: number | null;
  delivered: number | null;
  noShow: number | null;
  abandoned: number | null;
  driveflowUrl: string;
  history: HistoryPoint[];
};

export type CentresData = {
  meta: {
    period: string;
    lastUpdated: string;
    lastUpdatedLabel: string;
    citation: string;
    citationLong?: string;
    siteName?: string;
    siteUrl: string;
    author?: { name: string; url: string };
    national: {
      passRate: number;
      waitWeeks: number;
      delivered: number;
      noShow: number;
      abandoned: number;
    };
    periods?: PeriodMeta[];
    julyPeriods?: PeriodMeta[];
    nationalHistory?: HistoryPoint[];
    dataSource?: {
      publisher: string;
      url: string;
      tables: string[];
      downloaded: string;
    };
  };
  centres: Centre[];
};

export type CentreWithTrends = Centre & {
  passRateDelta: number | null;
  waitWeeksDelta: number | null;
  deliveredDelta: number | null;
  noShowDelta: number | null;
  abandonedDelta: number | null;
};

export const data = raw as CentresData;

function delta(history: HistoryPoint[], key: MetricKey): number | null {
  const points = history.filter((h) => h[key] != null);
  if (points.length < 2) return null;
  const current = points[points.length - 1][key] as number;
  const previous = points[points.length - 2][key] as number;
  return Math.round((current - previous) * 10) / 10;
}

export function withTrends(centre: Centre): CentreWithTrends {
  return {
    ...centre,
    passRateDelta: delta(centre.history, 'passRate'),
    waitWeeksDelta: delta(centre.history, 'waitWeeks'),
    deliveredDelta: delta(centre.history, 'delivered'),
    noShowDelta: delta(centre.history, 'noShow'),
    abandonedDelta: delta(centre.history, 'abandoned'),
  };
}

export function allCentresWithTrends(): CentreWithTrends[] {
  return data.centres.map(withTrends);
}

export function getCentre(slug: string): CentreWithTrends | undefined {
  const centre = data.centres.find((c) => c.slug === slug);
  return centre ? withTrends(centre) : undefined;
}

export function counties(): string[] {
  return [...new Set(data.centres.map((c) => c.county))].sort((a, b) =>
    a.localeCompare(b),
  );
}

export function allPeriods(): PeriodMeta[] {
  return data.meta.periods ?? [];
}

export function julyPeriods(): PeriodMeta[] {
  return data.meta.julyPeriods ?? allPeriods().filter((p) => p.period.endsWith('-07'));
}

export function valueAt(centre: Centre, period: string, key: MetricKey): number | null {
  const hit = centre.history.find((h) => h.period === period);
  if (!hit) return null;
  const v = hit[key];
  return v == null ? null : v;
}

export function formatPeriod(period: string): string {
  const [y, m] = period.split('-').map(Number);
  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];
  if (!y || !m || m < 1 || m > 12) return period;
  return `${months[m - 1]} ${y}`;
}

export function formatDelta(value: number | null, unit: 'pp' | 'w' | 'n' = 'n'): string {
  if (value === null) return '—';
  const sign = value > 0 ? '+' : '';
  if (unit === 'pp') return `${sign}${value} pp`;
  if (unit === 'w') return `${sign}${value} w`;
  return `${sign}${value}`;
}

export function formatPassRate(value: number | null): string {
  if (value == null) return 'Not published';
  return `${value}%`;
}

export function formatWait(value: number | null): string {
  if (value == null) return 'Not published';
  return `${value} weeks`;
}

export function formatCount(value: number | null): string {
  if (value == null) return 'Not published';
  return value.toLocaleString('en-IE');
}

export function nationalAt(period: string): HistoryPoint | undefined {
  return data.meta.nationalHistory?.find((h) => h.period === period);
}

export function dataRangeLabel(): string {
  const periods = allPeriods();
  if (!periods.length) return data.meta.lastUpdatedLabel;
  return `${formatPeriod(periods[0].period)} – ${formatPeriod(periods[periods.length - 1].period)}`;
}

/** Shift YYYY-MM by n months. */
export function shiftPeriod(period: string, months: number): string {
  const [y, m] = period.split('-').map(Number);
  const d = new Date(Date.UTC(y, m - 1 + months, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

/** Ireland rank by pass rate (1 = highest). Null if unpublished. */
export function passRateRank(centre: Centre, peers = data.centres): {
  rank: number | null;
  of: number;
} {
  const ranked = peers
    .filter((c) => c.passRate != null)
    .sort((a, b) => (b.passRate as number) - (a.passRate as number));
  if (centre.passRate == null) return { rank: null, of: ranked.length };
  const idx = ranked.findIndex((c) => c.slug === centre.slug);
  return { rank: idx >= 0 ? idx + 1 : null, of: ranked.length };
}

/** Change in a metric vs ~12 months earlier. */
export function changeOverMonths(
  centre: Centre,
  key: MetricKey,
  months = 12,
): number | null {
  const latest = centre.history.filter((h) => h[key] != null).at(-1);
  if (!latest || latest[key] == null) return null;
  const target = shiftPeriod(latest.period, -months);
  const earlier = centre.history.find((h) => h.period === target);
  if (!earlier || earlier[key] == null) {
    // Fall back to nearest earlier point at least ~10 months back
    const older = [...centre.history]
      .filter((h) => h.period <= target && h[key] != null)
      .at(-1);
    if (!older || older[key] == null) return null;
    return Math.round(((latest[key] as number) - (older[key] as number)) * 10) / 10;
  }
  return Math.round(((latest[key] as number) - (earlier[key] as number)) * 10) / 10;
}

export type ExplorerPayload = {
  meta: {
    period: string;
    lastUpdatedLabel: string;
    national: CentresData['meta']['national'];
    nationalHistory: HistoryPoint[];
  };
  centres: Array<{
    slug: string;
    name: string;
    county: string;
    passRate: number | null;
    waitWeeks: number | null;
    delivered: number | null;
    noShow: number | null;
    abandoned: number | null;
    passRateRank: number | null;
    rankOf: number;
    passRate12m: number | null;
    waitWeeks12m: number | null;
    driveflowUrl: string;
    history: HistoryPoint[];
  }>;
};

export function explorerPayload(): ExplorerPayload {
  const centres = data.centres;
  const withPass = centres.filter((c) => c.passRate != null).length;
  return {
    meta: {
      period: data.meta.period,
      lastUpdatedLabel: data.meta.lastUpdatedLabel,
      national: data.meta.national,
      nationalHistory: data.meta.nationalHistory ?? [],
    },
    centres: centres.map((c) => {
      const { rank, of } = passRateRank(c, centres);
      return {
        slug: c.slug,
        name: c.name,
        county: c.county,
        passRate: c.passRate,
        waitWeeks: c.waitWeeks,
        delivered: c.delivered,
        noShow: c.noShow,
        abandoned: c.abandoned,
        passRateRank: rank,
        rankOf: of || withPass,
        passRate12m: changeOverMonths(c, 'passRate', 12),
        waitWeeks12m: changeOverMonths(c, 'waitWeeks', 12),
        driveflowUrl:
          c.driveflowUrl || `https://www.driveflow.ie/${c.slug}-routes.html`,
        history: c.history,
      };
    }),
  };
}

const coords = coordsRaw as Record<string, { lat: number; lng: number }>;

export type MapCentre = ExplorerPayload['centres'][number] & {
  lat: number;
  lng: number;
};

export function mapPayload(): {
  meta: ExplorerPayload['meta'];
  centres: MapCentre[];
} {
  const base = explorerPayload();
  return {
    meta: base.meta,
    centres: base.centres
      .map((c) => {
        const loc = coords[c.slug];
        if (!loc) return null;
        return { ...c, lat: loc.lat, lng: loc.lng };
      })
      .filter((c): c is MapCentre => c != null),
  };
}
