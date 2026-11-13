import { useEffect, useState, type KeyboardEvent, type PointerEvent } from 'react'
import { getFareRows, type FareRow } from '../../services/api'
import styles from './FareChart.module.css'

// Plot geometry in viewBox units; the SVG scales to its container width
const W = 600, H = 280
const PAD = { top: 16, right: 116, bottom: 36, left: 44 }
const PLOT_W = W - PAD.left - PAD.right
const PLOT_H = H - PAD.top - PAD.bottom

/** How the jeepney fare grows with distance, regular vs discounted, from the matrix in effect. */
export default function FareChart() {
  const [rows, setRows] = useState<FareRow[] | null>(null)
  const [failed, setFailed] = useState(false)
  const [active, setActive] = useState<number | null>(null)  // index of the hovered kilometer

  useEffect(() => {
    getFareRows('traditional_jeepney')
      .then(setRows)
      .catch((err) => { console.error('Fare chart: could not load fare rows', err); setFailed(true) })
  }, [])

  if (failed) return <p className={styles.note}>The fare chart couldn't load. The fare checker still works.</p>
  if (!rows) return <div className={styles.skeleton} aria-label="Loading fare chart" />
  if (rows.length === 0) return null

  const maxKm = rows[rows.length - 1].distance_km
  const maxFare = Math.ceil(Math.max(...rows.map((r) => r.regular_fare)) / 10) * 10
  const x = (km: number) => PAD.left + ((km - 1) / Math.max(1, maxKm - 1)) * PLOT_W
  const y = (fare: number) => PAD.top + PLOT_H - (fare / maxFare) * PLOT_H
  const line = (key: 'regular_fare' | 'discounted_fare') =>
    rows.map((r, i) => `${i ? 'L' : 'M'}${x(r.distance_km)},${y(r[key])}`).join('')

  const yTicks = Array.from({ length: 5 }, (_, i) => (maxFare / 4) * i)
  const xTicks = rows.filter((r) => r.distance_km === 1 || r.distance_km % 5 === 0).map((r) => r.distance_km)
  const last = rows[rows.length - 1]
  const hovered = active !== null ? rows[active] : null

  // Snap the crosshair to the nearest kilometer under the pointer
  const onPointerMove = (e: PointerEvent<SVGSVGElement>) => {
    const box = e.currentTarget.getBoundingClientRect()
    const plotX = ((e.clientX - box.left) / box.width) * W
    // Clamp to the plotted range so the margins snap to the first or last kilometer
    const km = Math.min(maxKm, Math.max(1, Math.round(((plotX - PAD.left) / PLOT_W) * (maxKm - 1)) + 1))
    setActive(Math.max(0, rows.findIndex((r) => r.distance_km >= km)))
  }
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(rows.length - 1, Math.max(0, (i ?? -step) + step)))
  }

  return (
    <figure className={styles.figure}>
      <figcaption className={styles.title}>Jeepney fare by distance</figcaption>
      <p className={styles.subtitle}>From the fare matrix in effect. Use ← → to read each kilometer.</p>

      <ul className={styles.legend}>
        <li><span className={styles.swatch} style={{ background: 'var(--sky-text)' }} />Regular</li>
        <li><span className={styles.swatch} style={{ background: 'var(--orange-text)' }} />Student / Senior / PWD</li>
      </ul>

      <div className={styles.plot}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className={styles.svg}
          role="img"
          aria-label={`Line chart: the regular fare rises from ₱${rows[0].regular_fare.toFixed(2)} at 1 km to ₱${last.regular_fare.toFixed(2)} at ${maxKm} km; the discounted fare from ₱${rows[0].discounted_fare.toFixed(2)} to ₱${last.discounted_fare.toFixed(2)}.`}
          tabIndex={0}
          onPointerMove={onPointerMove}
          onPointerLeave={() => setActive(null)}
          onKeyDown={onKeyDown}
          onBlur={() => setActive(null)}
        >
          {/* Recessive grid and axes */}
          {yTicks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={PAD.left + PLOT_W} y1={y(t)} y2={y(t)} className={styles.grid} />
              <text x={PAD.left - 8} y={y(t)} className={styles.axis} textAnchor="end" dominantBaseline="middle">₱{t}</text>
            </g>
          ))}
          {xTicks.map((km) => (
            <text key={km} x={x(km)} y={H - PAD.bottom + 18} className={styles.axis} textAnchor="middle">{km} km</text>
          ))}

          <path d={line('regular_fare')} className={styles.line} stroke="var(--sky-text)" />
          <path d={line('discounted_fare')} className={styles.line} stroke="var(--orange-text)" />

          {/* Direct labels at the line ends */}
          <text x={x(maxKm) + 8} y={y(last.regular_fare)} className={styles.endLabel} dominantBaseline="middle">₱{last.regular_fare.toFixed(0)} regular</text>
          <text x={x(maxKm) + 8} y={y(last.discounted_fare)} className={styles.endLabel} dominantBaseline="middle">₱{last.discounted_fare.toFixed(0)} discounted</text>

          {hovered && (
            <g>
              <line x1={x(hovered.distance_km)} x2={x(hovered.distance_km)} y1={PAD.top} y2={PAD.top + PLOT_H} className={styles.crosshair} />
              <circle cx={x(hovered.distance_km)} cy={y(hovered.regular_fare)} r={5} fill="var(--sky-text)" className={styles.marker} />
              <circle cx={x(hovered.distance_km)} cy={y(hovered.discounted_fare)} r={5} fill="var(--orange-text)" className={styles.marker} />
            </g>
          )}
        </svg>

        {hovered && (
          <div
            className={styles.tooltip}
            style={{ left: `${(x(hovered.distance_km) / W) * 100}%` }}
            role="status"
          >
            <strong>{hovered.distance_km} km</strong>
            <span><i style={{ background: 'var(--sky-text)' }} />Regular ₱{hovered.regular_fare.toFixed(2)}</span>
            <span><i style={{ background: 'var(--orange-text)' }} />Discounted ₱{hovered.discounted_fare.toFixed(2)}</span>
          </div>
        )}
      </div>

      {/* The same numbers as a table, for screen readers and anyone who prefers exact values */}
      <details className={styles.tableToggle}>
        <summary>Show as table</summary>
        <table className={styles.table}>
          <thead><tr><th scope="col">Distance</th><th scope="col">Regular</th><th scope="col">Discounted</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.distance_km}>
                <td>{r.distance_km} km</td>
                <td>₱{r.regular_fare.toFixed(2)}</td>
                <td>₱{r.discounted_fare.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  )
}
