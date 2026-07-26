import { NavLink, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { logout } from '../../services/authService';
import { getClassrooms } from '../../services/classroomService';
import api from '../../services/api';
import type { Classroom } from '../../types/classroom';
import styles from './Sidebar.module.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const navigate = useNavigate();
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [userName, setUserName] = useState<string>('');

  useEffect(() => {
    getClassrooms()
      .then((data) => setClassrooms(Array.isArray(data) ? data : []))
      .catch(() => setClassrooms([]));

    api.get<{ name: string }>('/auth/me')
      .then((res) => setUserName(res.data.name))
      .catch(() => setUserName('Usuario'));
  }, []);

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
          <div className={styles.avatar}>{userName ? userName.charAt(0).toUpperCase() : 'U'}</div>
          <div className={styles.userInfo}>
            <span className={styles.username}>{userName || 'Usuario'}</span>
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
          <button
            className={styles.newBtn}
            onClick={() => navigate('/dashboard/classes')}
          >
            + Nueva clase
          </button>
        </div>

        <div className={styles.divider} />

        {/* Navigation links */}
        <nav className={styles.nav}>
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
          {classrooms.length === 0 && (
            <div className={styles.classItem} style={{ opacity: 0.5, fontSize: '0.8rem' }}>
              Sin clases aún
            </div>
          )}
          {classrooms.map((c) => (
            <div
              key={c.id}
              className={styles.classItem}
              onClick={() => navigate(`/dashboard/class/${c.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  navigate(`/dashboard/class/${c.id}`);
                }
              }}
            >
              <span className={styles.classDot} />
              {c.name}
            </div>
          ))}
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
