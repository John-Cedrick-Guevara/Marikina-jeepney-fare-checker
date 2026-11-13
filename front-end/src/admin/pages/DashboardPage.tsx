import { useEffect, useState } from 'react'
import { adminApi, formatDate, type AuditEntry, type Stats } from '../adminApi'
import Icon from '../../components/Icon/Icon'
import styles from '../admin.module.css'
import dash from './DashboardPage.module.css'

/**
 * KPI targets the team monitors (see the O&M KPI slide). A KPI with no data yet shows no status.
 * ponytail: targets are constants; move to a settings table if admins need to change them.
 */
const TARGETS = {
  successRate: 0.9,       // at least 90% of lookups return a fare
  unsupportedRate: 0.1,   // at most 10% of lookups are trips no route covers
  responseMs: 500,        // average estimate under half a second
  fareDataAgeDays: 365,   // the fare matrix in effect was issued within a year
}

const RANGES = [7, 30, 90]

const pct = (v: number | null) => (v === null ? '—' : `${Math.round(v * 100)}%`)

/** KPI monitoring: fare lookup volume and quality, fare data freshness, and recent admin changes. */
export default function DashboardPage() {
  const [days, setDays] = useState(30)
  const [stats, setStats] = useState<Stats | null>(null)
  const [audit, setAudit] = useState<AuditEntry[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setStats(null)
    adminApi.stats(days).then(setStats).catch((err) => setError(err.message))
  }, [days])
  useEffect(() => { adminApi.auditLog().then(setAudit).catch((err) => setError(err.message)) }, [])

  return (
    <>
      <h1 className={styles.title}>Dashboard</h1>
      <p className={styles.subtitle}>How commuters use the fare checker, and whether it meets its targets.</p>

      <div className={dash.range} role="group" aria-label="Time range">
        {RANGES.map((d) => (
          <button key={d} className={`${styles.button} ${styles.small} ${d === days ? styles.primary : ''}`}
                  aria-pressed={d === days} onClick={() => setDays(d)}>
            Last {d} days
          </button>
        ))}
      </div>

      {error && <p className={styles.error} role="alert">{error}</p>}

      {!stats ? <div className={dash.skeleton} aria-label="Loading dashboard" /> : (
        <>
          <div className={dash.tiles}>
            <Tile label="Fare lookups" value={stats.total_lookups.toLocaleString()} />
            <Tile label="Returned a fare" value={pct(stats.success_rate)} target={`Target ≥ ${pct(TARGETS.successRate)}`}
                  ok={stats.success_rate === null ? null : stats.success_rate >= TARGETS.successRate} />
            <Tile label="Unsupported trips" value={pct(stats.unsupported_rate)} target={`Target ≤ ${pct(TARGETS.unsupportedRate)}`}
                  ok={stats.unsupported_rate === null ? null : stats.unsupported_rate <= TARGETS.unsupportedRate} />
            <Tile label="Avg. response" value={stats.avg_response_ms === null ? '—' : `${Math.round(stats.avg_response_ms)} ms`}
                  target={`Target ≤ ${TARGETS.responseMs} ms`}
                  ok={stats.avg_response_ms === null ? null : stats.avg_response_ms <= TARGETS.responseMs} />
          </div>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Lookups per day</h2>
            <DailyChart daily={stats.daily} days={days} />
          </section>

          <div className={dash.columns}>
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Most searched trips</h2>
              {stats.top_trips.length === 0 ? <p className={styles.empty}>No lookups in this range yet.</p> : (
                <table className={styles.table}>
                  <thead><tr><th>Trip</th><th className={styles.num}>Lookups</th></tr></thead>
                  <tbody>
                    {stats.top_trips.map((t) => (
                      <tr key={`${t.origin}-${t.destination}`}>
                        <td>{t.origin} → {t.destination}</td>
                        <td className={styles.num}>{t.lookups}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Fare data freshness</h2>
              <table className={styles.table}>
                <thead><tr><th>PUV type</th><th>In effect since</th><th>Status</th></tr></thead>
                <tbody>
                  {stats.fare_data.map((f) => (
                    <tr key={f.puv_type}>
                      <td>{f.label}</td>
                      <td>{f.effective_from ? `${formatDate(f.effective_from)} (${f.age_days} days)` : '—'}</td>
                      <td><Status ok={f.age_days === null ? false : f.age_days <= TARGETS.fareDataAgeDays}
                                  okText="Current" badText={f.age_days === null ? 'No matrix' : 'Review'} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        </>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent admin changes</h2>
        {audit === null ? <p className={styles.empty}>Loading…</p> : audit.length === 0 ? (
          <p className={styles.empty}>No admin changes recorded yet.</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead><tr><th>When</th><th>Admin</th><th>Action</th><th className={styles.num}>Result</th></tr></thead>
              <tbody>
                {audit.map((a, i) => (
                  <tr key={i}>
                    <td>{new Date(a.created_at).toLocaleString('en-PH')}</td>
                    <td>{a.admin_email}</td>
                    <td><code>{a.method} {a.path}</code></td>
                    <td className={styles.num}>{a.status_code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}

function Tile({ label, value, target, ok }: { label: string; value: string; target?: string; ok?: boolean | null }) {
  return (
    <div className={dash.tile}>
      <p className={dash.tileLabel}>{label}</p>
      <p className={dash.tileValue}>{value}</p>
      {target && (
        <p className={dash.tileTarget}>
          {target}
          {ok !== null && ok !== undefined && <> · <Status ok={ok} okText="On target" badText="Off target" /></>}
        </p>
      )}
    </div>
  )
}

/** Status is never colour alone: an icon and a word go with it. */
function Status({ ok, okText, badText }: { ok: boolean; okText: string; badText: string }) {
  return (
    <span className={ok ? dash.ok : dash.bad}>
      <Icon name={ok ? 'check' : 'alert'} /> {ok ? okText : badText}
    </span>
  )
}

/** One bar per day of the range (days without lookups show as empty), single series. */
function DailyChart({ daily, days }: { daily: Stats['daily']; days: number }) {
  const [active, setActive] = useState<number | null>(null)
  const byDay = new Map(daily.map((d) => [d.day, d]))
  const today = new Date()
  const series = Array.from({ length: days }, (_, i) => {
    const date = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (days - 1 - i))
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    return { key, date, lookups: byDay.get(key)?.lookups ?? 0, withFare: byDay.get(key)?.with_fare ?? 0 }
  })
  const max = Math.max(1, ...series.map((d) => d.lookups))
  const W = 600, H = 180, left = 32, bottom = 22, plotH = H - bottom - 8
  const slot = (W - left) / days
  const barW = Math.max(2, slot - 2)  // 2px gap between bars
  const shown = active !== null ? series[active] : null
  const label = (d: Date) => d.toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })

  return (
    <div className={dash.chart}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" className={dash.chartSvg}
           aria-label={`Bar chart of fare lookups per day over the last ${days} days, peaking at ${max}.`}
           onPointerLeave={() => setActive(null)}>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={left} x2={W} y1={8 + plotH * (1 - f)} y2={8 + plotH * (1 - f)} className={dash.grid} />
            <text x={left - 6} y={8 + plotH * (1 - f)} className={dash.axis} textAnchor="end" dominantBaseline="middle">
              {Math.round(max * f)}
            </text>
          </g>
        ))}
        {series.map((d, i) => {
          const h = (d.lookups / max) * plotH
          return (
            <g key={d.key} onPointerEnter={() => setActive(i)}>
              {/* Hit target is the whole column, bigger than the bar */}
              <rect x={left + i * slot} y={8} width={slot} height={plotH} fill="transparent" />
              {h > 0 && <rect x={left + i * slot + 1} y={8 + plotH - h} width={barW} height={h} rx={Math.min(4, barW / 2)}
                              fill="var(--sky-text)" opacity={active === null || active === i ? 1 : 0.45} />}
            </g>
          )
        })}
        <text x={left} y={H - 4} className={dash.axis}>{label(series[0].date)}</text>
        <text x={W} y={H - 4} className={dash.axis} textAnchor="end">{label(series[days - 1].date)}</text>
      </svg>
      {shown && (
        <div className={dash.tooltip} style={{ left: `${((left + (active! + 0.5) * slot) / W) * 100}%` }} role="status">
          <strong>{label(shown.date)}</strong>
          <span>{shown.lookups} lookups · {shown.withFare} with a fare</span>
        </div>
      )}
    </div>
  )
}
