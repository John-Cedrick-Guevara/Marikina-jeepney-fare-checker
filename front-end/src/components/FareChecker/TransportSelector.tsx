import type { PuvType } from '../../services/api'
import Icon, { type IconName } from '../Icon/Icon'
import styles from './TransportSelector.module.css'

export const TRANSPORT_OPTIONS: { id: PuvType; label: string; sub: string; icon: IconName }[] = [
  { id: 'traditional_jeepney', label: 'Jeepney', sub: 'Traditional', icon: 'jeepney' },
  { id: 'modern_jeepney', label: 'Beep Jeep', sub: 'Modern / E-Jeep', icon: 'ejeep' },
]

export const transportLabel = (id: PuvType) =>
  TRANSPORT_OPTIONS.find((o) => o.id === id)?.label ?? id

interface Props {
  value: PuvType
  onChange: (value: PuvType) => void
  /** PUV types without a fare matrix in effect; shown as "Fares coming soon" */
  unavailable: PuvType[]
}

export default function TransportSelector({ value, onChange, unavailable }: Props) {
  return (
    <div
      className={styles.group}
      role="group"
      aria-label="Choose transport type"
    >
      {TRANSPORT_OPTIONS.map((opt) => {
        const active = value === opt.id
        return (
          <button
            key={opt.id}
            type="button"
            className={`${styles.btn} ${active ? styles.active : ''}`}
            onClick={() => onChange(opt.id)}
            aria-pressed={active}
          >
            <span className={styles.icon}><Icon name={opt.icon} /></span>
            <span className={styles.labelWrap}>
              <span className={styles.label}>{opt.label}</span>
              <span className={styles.sub}>{unavailable.includes(opt.id) ? 'Fares coming soon' : opt.sub}</span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
