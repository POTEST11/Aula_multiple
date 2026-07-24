import { Link } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import styles from './HomePage.module.css';

export default function HomePage() {
  return (
    <div className={styles.page}>
      <Navbar />

      {/* Section 1: Hero */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>Enseña a todos, inspira a cada uno</h1>
          <p className={styles.heroSubtitle}>
            Genera actividades diferenciadas por grado para tu aula multigrado
            con inteligencia artificial
          </p>
          <Link to="/register" className={styles.heroCta}>
            Empezar gratis &rarr;
          </Link>
        </div>
        <div className={styles.heroIllustration}>
          {/* Ilustración: docente frente a grupo multigrado con burbujas de actividades */}
          <span className={styles.placeholderText}>Ilustración principal</span>
        </div>
      </section>

      {/* Section 2: Características */}
      <section id="caracteristicas" className={styles.features}>
        <h2 className={styles.sectionTitle}>¿Qué puedes hacer?</h2>
        <div className={styles.featureGrid}>
          <div className={`${styles.featureCard} ${styles.cardGreen}`}>
            <div className={styles.featureIconArea}>
              {/* Placeholder: ícono/ilustración IA generativa */}
              <span className={styles.iconPlaceholder}>IA</span>
            </div>
            <h3 className={styles.featureTitle}>Generación con IA</h3>
            <p className={styles.featureDesc}>
              Crea actividades adaptadas a múltiples niveles con un solo clic,
              usando inteligencia artificial.
            </p>
          </div>

          <div className={`${styles.featureCard} ${styles.cardPurple}`}>
            <div className={styles.featureIconArea}>
              {/* Placeholder: ícono/ilustración estándares */}
              <span className={styles.iconPlaceholder}>AC</span>
            </div>
            <h3 className={styles.featureTitle}>Alineación curricular</h3>
            <p className={styles.featureDesc}>
              Las actividades se alinean automáticamente con los estándares
              curriculares de tu país.
            </p>
          </div>

          <div className={`${styles.featureCard} ${styles.cardBlue}`}>
            <div className={styles.featureIconArea}>
              {/* Placeholder: ícono/ilustración aula */}
              <span className={styles.iconPlaceholder}>GC</span>
            </div>
            <h3 className={styles.featureTitle}>Gestión de clases</h3>
            <p className={styles.featureDesc}>
              Organiza tus grupos multigrado y define los grados que atiendes en
              cada clase.
            </p>
          </div>

          <div className={`${styles.featureCard} ${styles.cardOrange}`}>
            <div className={styles.featureIconArea}>
              {/* Placeholder: ícono/ilustración archivo */}
              <span className={styles.iconPlaceholder}>HR</span>
            </div>
            <h3 className={styles.featureTitle}>Historial reutilizable</h3>
            <p className={styles.featureDesc}>
              Guarda y reutiliza todas las actividades que has generado.
              Filtra por materia, clase o fecha.
            </p>
          </div>
        </div>
      </section>

      {/* Section 3: Cómo funciona */}
      <section id="como-funciona" className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>Así de fácil</h2>
        <div className={styles.stepsContainer}>
          <div className={styles.step}>
            <div className={styles.stepBadge}>1</div>
            <div className={styles.stepIllustration}>
              {/* Placeholder: ilustración crear clase */}
              <span className={styles.placeholderText}>Crear clase</span>
            </div>
            <p className={styles.stepText}>Crea tu clase con los grados</p>
          </div>

          <div className={styles.stepDot} />

          <div className={styles.step}>
            <div className={`${styles.stepBadge} ${styles.stepBadge2}`}>2</div>
            <div className={styles.stepIllustration}>
              {/* Placeholder: ilustración chat */}
              <span className={styles.placeholderText}>Pedir actividad</span>
            </div>
            <p className={styles.stepText}>Pide una actividad sobre cualquier tema</p>
          </div>

          <div className={styles.stepDot} />

          <div className={styles.step}>
            <div className={`${styles.stepBadge} ${styles.stepBadge3}`}>3</div>
            <div className={styles.stepIllustration}>
              {/* Placeholder: ilustración resultados */}
              <span className={styles.placeholderText}>Resultados</span>
            </div>
            <p className={styles.stepText}>Recibe variantes adaptadas por nivel</p>
          </div>
        </div>
      </section>

      {/* Section 4: CTA final */}
      <section className={styles.ctaSection}>
        <h2 className={styles.ctaTitle}>¿Listo para transformar tu aula?</h2>
        <p className={styles.ctaSubtitle}>
          Únete gratis y comienza a generar actividades en minutos
        </p>
        <Link to="/register" className={styles.ctaButton}>
          Registrarse gratis
        </Link>
      </section>

      {/* Section 5: Footer */}
      <footer className={styles.footer} id="contacto">
        <div className={styles.footerLinks}>
          <a href="#" className={styles.footerLink}>Términos</a>
          <span className={styles.footerSep}>|</span>
          <a href="#" className={styles.footerLink}>Privacidad</a>
          <span className={styles.footerSep}>|</span>
          <a href="#contacto" className={styles.footerLink}>Contacto</a>
        </div>
        <p className={styles.footerCopy}>&copy; 2025 Aula Múltiple</p>
      </footer>
    </div>
  );
}
