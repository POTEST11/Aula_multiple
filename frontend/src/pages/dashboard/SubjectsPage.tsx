import { useEffect, useState, useCallback } from 'react';
import type { Subject } from '../../types/subject';
import {
  getSubjects,
  createSubject,
  deleteSubject,
} from '../../services/subjectService';
import styles from './SubjectsPage.module.css';

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Inline form state
  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Delete confirm state
  const [deleteTarget, setDeleteTarget] = useState<Subject | null>(null);

  const fetchSubjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSubjects();
      setSubjects(Array.isArray(data) ? data : []);
    } catch {
      setSubjects([]);
      setError('No se pudieron cargar las materias. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  function openForm() {
    setFormName('');
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setFormName('');
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) return;

    setSubmitting(true);
    try {
      const created = await createSubject({ name: formName.trim() });
      setSubjects((prev) => [...prev, created]);
      closeForm();
    } catch {
      // Keep form open on error so user can retry
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deleteSubject(deleteTarget.id);
      setSubjects((prev) => prev.filter((s) => s.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setDeleteTarget(null);
    }
  }

  function formatDate(dateStr: string) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  // Render
  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>Cargando materias...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorState}>
          <p>{error}</p>
          <button className={styles.retryBtn} onClick={fetchSubjects}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.title}>Mis Materias</h2>
        {!showForm && (
          <button
            className={styles.newBtn}
            onClick={openForm}
            aria-label="Crear nueva materia"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Nueva materia
          </button>
        )}
      </div>

      {/* Inline creation form */}
      {showForm && (
        <form className={styles.inlineForm} onSubmit={handleCreate}>
          <input
            className={styles.inlineInput}
            type="text"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            placeholder="Nombre de la materia"
            autoFocus
            required
            aria-label="Nombre de la nueva materia"
          />
          <button
            type="submit"
            className={styles.submitBtn}
            disabled={!formName.trim() || submitting}
          >
            {submitting ? 'Creando...' : 'Crear'}
          </button>
          <button
            type="button"
            className={styles.cancelFormBtn}
            onClick={closeForm}
          >
            Cancelar
          </button>
        </form>
      )}

      {/* Empty state */}
      {subjects.length === 0 && (
        <div className={styles.emptyState}>
          <p>Aún no tienes materias creadas.</p>
          <button className={styles.newBtn} onClick={openForm}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Crear tu primera materia
          </button>
        </div>
      )}

      {/* Subjects list */}
      {subjects.length > 0 && (
        <div className={styles.list}>
          {subjects.map((subject) => (
            <div key={subject.id} className={styles.card}>
              <div className={styles.cardInfo}>
                <h3 className={styles.cardName}>{subject.name}</h3>
                <span className={styles.cardDate}>
                  Creada el {formatDate(subject.created_at)}
                </span>
              </div>
              <div className={styles.cardActions}>
                <button
                  className={styles.iconBtn}
                  onClick={() => setDeleteTarget(subject)}
                  aria-label={`Eliminar materia ${subject.name}`}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <div
          className={styles.confirmOverlay}
          onClick={() => setDeleteTarget(null)}
          role="alertdialog"
          aria-modal="true"
          aria-label="Confirmar eliminación"
        >
          <div className={styles.confirmDialog} onClick={(e) => e.stopPropagation()}>
            <p>
              ¿Estás seguro de que deseas eliminar la materia{' '}
              <strong>{deleteTarget.name}</strong>? El historial previamente
              generado se conservará como registros independientes.
            </p>
            <div className={styles.confirmActions}>
              <button
                className={styles.cancelBtn}
                onClick={() => setDeleteTarget(null)}
              >
                Cancelar
              </button>
              <button className={styles.deleteBtn} onClick={handleDelete}>
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
