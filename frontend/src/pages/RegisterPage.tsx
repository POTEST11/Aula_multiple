import { type FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import styles from './AuthPage.module.css';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { loading, error, handleRegister } = useAuth();

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    handleRegister({ name, email, password });
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Crear Cuenta</h1>
        <p className={styles.subtitle}>
          Regístrate para empezar a generar actividades
        </p>

        <form className={styles.form} onSubmit={onSubmit}>
          {error && <p className={styles.error}>{error}</p>}

          <input
            className={styles.input}
            type="text"
            placeholder="Nombre completo"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
          />

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
            placeholder="Contraseña (mín. 8 caracteres)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />

          <button
            className={styles.submitBtn}
            type="submit"
            disabled={loading}
          >
            {loading ? 'Creando cuenta...' : 'Registrarse'}
          </button>
        </form>

        <Link to="/login" className={styles.link}>
          ¿Ya tienes cuenta? Inicia sesión
        </Link>
        <Link to="/" className={styles.backLink}>
          &larr; Volver al inicio
        </Link>
      </div>
    </div>
  );
}
