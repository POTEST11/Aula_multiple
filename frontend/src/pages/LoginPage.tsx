import { type FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import styles from './AuthPage.module.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { loading, error, handleLogin } = useAuth();

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    handleLogin({ email, password });
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Iniciar Sesión</h1>
        <p className={styles.subtitle}>
          Ingresa tus credenciales para continuar
        </p>

        <form className={styles.form} onSubmit={onSubmit}>
          {error && <p className={styles.error}>{error}</p>}

          <input
            className={styles.input}
            type="email"
            placeholder="Correo electrónico"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <input
            className={styles.input}
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <button
            className={styles.submitBtn}
            type="submit"
            disabled={loading}
          >
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        <Link to="/register" className={styles.link}>
          ¿No tienes cuenta? Regístrate
        </Link>
        <Link to="/" className={styles.backLink}>
          &larr; Volver al inicio
        </Link>
      </div>
    </div>
  );
}
