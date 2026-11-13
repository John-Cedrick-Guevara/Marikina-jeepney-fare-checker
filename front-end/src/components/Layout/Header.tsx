import { Link } from 'react-router-dom'
import Icon from '../Icon/Icon'
import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header}>
      <Link to="/" className={styles.logo} aria-label="Commute.ph home">
        <div className={styles.logoIcon} aria-hidden="true"><Icon name="jeepney" /></div>
        <span className={styles.logoText}>
          commute<span className={styles.dot}>.</span>ph
        </span>
      </Link>

      <span className={styles.tagline}>Know your fare. Enjoy the ride.</span>

      <Link to="/how-it-works" className={styles.hiwBtn}>
        How it works <Icon name="arrowRight" />
      </Link>
    </header>
  )
}
