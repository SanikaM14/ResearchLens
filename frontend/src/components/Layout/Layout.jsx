import { NavLink } from 'react-router-dom';
import styles from './Layout.module.css';

export default function Layout({ children }) {
  return (
    <div className={styles.container}>
      <header className={styles.topBrand}>
        <h1>ResearchLens</h1>
        <p>Evidence-Grounded Research Intelligence</p>
      </header>
      
      <main className={styles.main}>
        {children}
      </main>

      <nav className={styles.bottomNav}>
        <div className={styles.navInner}>
          <NavLink to="/" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <i className="bi bi-grid"></i>
            <span>Dashboard</span>
          </NavLink>
          
          <NavLink to="/analysis" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <i className="bi bi-file-text"></i>
            <span>Analysis</span>
          </NavLink>

          <NavLink to="/workspace" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem} id={styles.centerCta}>
            <div className={styles.ctaCircle}>
              <i className="bi bi-search"></i>
            </div>
          </NavLink>

          <NavLink to="/compare" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <i className="bi bi-intersect"></i>
            <span>Compare</span>
          </NavLink>

          <NavLink to="/verify" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <i className="bi bi-check-circle"></i>
            <span>Verify</span>
          </NavLink>

          <NavLink to="/podcast" className={({ isActive }) => isActive ? `${styles.navItem} ${styles.active}` : styles.navItem}>
            <i className="bi bi-mic"></i>
            <span>Audio</span>
          </NavLink>
        </div>
      </nav>
    </div>
  );
}
