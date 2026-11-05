import styles from './LocationInput.module.css'

/**
 * Stop picker. Only known stops can be chosen, since fares exist only for stored routes.
 * `value` and `onChange` use a stop object ({ id, point_name }) or null.
 * `disabledName` greys out the stop already chosen in the other field.
 */
export default function LocationInput({
  id,
  label,
  icon,
  stops,
  value,
  onChange,
  placeholder,
  disabledName,
  disabled,
  error,
}) {
  const handleChange = (e) => {
    onChange(stops.find((s) => s.id === e.target.value) ?? null)
  }

  return (
    <div className={`${styles.wrapper} ${error ? styles.hasError : ''}`}>
      <div className={styles.field}>
        <span className={styles.icon} aria-hidden="true">{icon}</span>
        <div className={styles.inputWrap}>
          <label htmlFor={id} className={styles.label}>{label}</label>
          <select
            id={id}
            value={value?.id ?? ''}
            onChange={handleChange}
            disabled={disabled}
            className={`${styles.input} ${value ? '' : styles.placeholder}`}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${id}-error` : undefined}
          >
            <option value="" disabled>{placeholder}</option>
            {stops.map((stop) => (
              <option key={stop.id} value={stop.id} disabled={stop.point_name === disabledName}>
                {stop.point_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <p id={`${id}-error`} className={styles.errorMsg} role="alert">⚠ {error}</p>
      )}
    </div>
  )
}
