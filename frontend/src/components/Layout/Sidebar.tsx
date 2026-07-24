import { NavLink, useNavigate } from 'react-router-dom';
import { logout } from '../../services/authService';
import styles from './Sidebar.module.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <>
      {/* Mobile overlay */}
      {!collapsed && (
        <div
          className={styles.overlay}
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
        {/* User area */}
        <div className={styles.userArea}>
          <div className={styles.avatar}>U</div>
          <div className={styles.userInfo}>
            <span className={styles.username}>Usuario</span>
          </div>
          <button
            className={styles.settingsBtn}
            onClick={handleLogout}
            aria-label="Cerrar sesión"
            title="Cerrar sesión"
          >
            {/* Settings/logout icon placeholder */}
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 14H3.33C2.6 14 2 13.4 2 12.67V3.33C2 2.6 2.6 2 3.33 2H6M10.67 11.33L14 8L10.67 4.67M14 8H6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        {/* New class button */}
        <div className={styles.newBtnWrap}>
          <button className={styles.newBtn}>+ Nueva clase</button>
        </div>

        <div className={styles.divider} />

        {/* Navigation links */}
        <nav className={styles.nav}>
          <NavLink
            to="/dashboard/generate"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            <svg className={styles.navIcon} width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2L11 7H16L12 10.5L13.5 16L9 12.5L4.5 16L6 10.5L2 7H7L9 2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
            </svg>
            <span>Generar</span>
          </NavLink>

          <NavLink
            to="/dashboard/history"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            <svg className={styles.navIcon} width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M9 5V9L12 11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
            <span>Historial</span>
          </NavLink>

          <NavLink
            to="/dashboard/classes"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            <svg className={styles.navIcon} width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="2" y="3" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M2 7H16" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M6 7V15" stroke="currentColor" strokeWidth="1.4"/>
            </svg>
            <span>Clases</span>
          </NavLink>

          <NavLink
            to="/dashboard/subjects"
            className={({ isActive }) =>
              `${styles.navLink} ${isActive ? styles.active : ''}`
            }
          >
            <svg className={styles.navIcon} width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 3H8V8H3V3Z" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M10 3H15V8H10V3Z" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M3 10H8V15H3V10Z" stroke="currentColor" strokeWidth="1.4"/>
              <path d="M10 10H15V15H10V10Z" stroke="currentColor" strokeWidth="1.4"/>
            </svg>
            <span>Materias</span>
          </NavLink>
        </nav>

        <div className={styles.divider} />

        {/* My Classes section */}
        <div className={styles.sectionLabel}>Mis Clases</div>
        <div className={styles.classList}>
          <div className={`${styles.classItem} ${styles.classItemActive}`}>
            <span className={styles.classDot} />
            3° Primaria A
          </div>
          <div className={styles.classItem}>
            <span className={styles.classDot} />
            5° Primaria B
          </div>
        </div>

        <div className={styles.divider} />

        {/* Multimedia section */}
        <div className={styles.sectionLabel}>Contenido multimedia</div>
        <div className={styles.mediaGrid}>
          <div className={styles.mediaThumbnail}>
            {/* Thumbnail: documento/media */}
          </div>
          <div className={styles.mediaThumbnail}>
            {/* Thumbnail: documento/media */}
          </div>
          <div className={styles.mediaThumbnail}>
            {/* Thumbnail: documento/media */}
          </div>
          <div className={styles.mediaThumbnail}>
            {/* Thumbnail: documento/media */}
          </div>
        </div>

        {/* Spacer pushes collapse button to bottom */}
        <div className={styles.spacer} />

        {/* Collapse toggle */}
        <button
          className={styles.collapseBtn}
          onClick={onToggle}
          aria-label={collapsed ? 'Expandir panel' : 'Colapsar panel'}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            {collapsed ? (
              <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            ) : (
              <path d="M10 3L5 8L10 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            )}
          </svg>
        </button>
      </aside>
    </>
  );
}
