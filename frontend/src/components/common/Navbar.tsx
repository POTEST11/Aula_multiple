import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TOKEN_KEY } from '../../services/api';
import { useTheme } from '../../hooks/useTheme';
import styles from './Navbar.module.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const isAuthenticated = Boolean(localStorage.getItem(TOKEN_KEY));
  const { resolvedTheme, toggleTheme } = useTheme();

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 20);
    }
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`${styles.navbar} ${scrolled ? styles.scrolled : ''}`}>
      <div className={styles.container}>
        {/* Logo */}
        <a href="#" className={styles.logo}>
          {/* Logo placeholder */}
          Aula Múltiple
        </a>

        {/* Center links - desktop */}
        <div className={styles.centerLinks}>
          <a href="#caracteristicas" className={styles.navLink}>Características</a>
          <a href="#como-funciona" className={styles.navLink}>Cómo funciona</a>
          <a href="#contacto" className={styles.navLink}>Contacto</a>
        </div>

        {/* Right buttons - desktop */}
        <div className={styles.rightActions}>
          <button
            className={styles.themeToggle}
            onClick={toggleTheme}
            aria-label={resolvedTheme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
            title={resolvedTheme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
          >
            {resolvedTheme === 'dark' ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {isAuthenticated ? (
            <Link to="/dashboard" className={styles.btnPrimary}>
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className={styles.btnGhost}>
                Iniciar sesión
              </Link>
              <Link to="/register" className={styles.btnPrimary}>
                Registrarse
              </Link>
            </>
          )}
        </div>

        {/* Hamburger - mobile */}
        <button
          className={styles.hamburger}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
        >
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen : ''}`} />
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen : ''}`} />
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen : ''}`} />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          <a href="#caracteristicas" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            Características
          </a>
          <a href="#como-funciona" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            Cómo funciona
          </a>
          <a href="#contacto" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            Contacto
          </a>
          <div className={styles.mobileDivider} />
          <button className={styles.mobileThemeToggle} onClick={toggleTheme}>
            {resolvedTheme === 'dark' ? '☀️ Modo claro' : '🌙 Modo oscuro'}
          </button>
          <div className={styles.mobileDivider} />
          {isAuthenticated ? (
            <Link to="/dashboard" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
                Iniciar sesión
              </Link>
              <Link to="/register" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
                Registrarse
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
