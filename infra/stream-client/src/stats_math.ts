// Summary maths for the session metrics (chunk 0.0 §c): medians and p95s over the per-second records.

/** Finite numbers only, sorted ascending. */
export function clean(values: ReadonlyArray<number | null | undefined>): number[] {
    return values.filter((v): v is number => typeof v === "number" && Number.isFinite(v)).sort((a, b) => a - b)
}

/** The q-quantile (0..1) by linear interpolation between closest ranks (numpy's default); null when empty. */
export function quantile(values: ReadonlyArray<number | null | undefined>, q: number): number | null {
    const s = clean(values)
    if (s.length === 0) return null
    const pos = (s.length - 1) * Math.min(1, Math.max(0, q))
    const lo = Math.floor(pos)
    const hi = Math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)
}

export const median = (values: ReadonlyArray<number | null | undefined>) => quantile(values, 0.5)
export const p95 = (values: ReadonlyArray<number | null | undefined>) => quantile(values, 0.95)

export type Summary = { n: number, median: number | null, p95: number | null, min: number | null, max: number | null, mean: number | null }

export function summarize(values: ReadonlyArray<number | null | undefined>): Summary {
    const s = clean(values)
    const round = (v: number | null) => v === null ? null : Math.round(v * 100) / 100
    return {
        n: s.length,
        median: round(quantile(s, 0.5)),
        p95: round(quantile(s, 0.95)),
        min: round(s.length ? s[0] : null),
        max: round(s.length ? s[s.length - 1] : null),
        mean: round(s.length ? s.reduce((a, b) => a + b, 0) / s.length : null),
    }
}

/** Summaries of named fields over a list of records: `{ rttMs: Summary, ... }`. */
export function summarizeFields<T extends object>(records: ReadonlyArray<T>, fields: ReadonlyArray<keyof T & string>): Record<string, Summary> {
    const out: Record<string, Summary> = {}
    for (const f of fields) out[f] = summarize(records.map((r) => r[f] as unknown as number))
    return out
}
