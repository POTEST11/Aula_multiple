import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Classroom, ClassroomCreate, ClassroomUpdate } from '../../types/classroom';
import {
  getClassrooms,
  createClassroom,
  updateClassroom,
  deleteClassroom,
} from '../../services/classroomService';
import styles from './ClassesPage.module.css';

const ACCENT_CLASSES = [
  styles.accentGreen,
  styles.accentPurple,
  styles.accentBlue,
  styles.accentOrange,
  styles.accentPink,
];

const AVAILABLE_GRADES = [2, 3, 4, 5, 6];

export default function ClassesPage() {
  const navigate = useNavigate();
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingClass, setEditingClass] = useState<Classroom | null>(null);
  const [formName, setFormName] = useState('');
  const [formGrades, setFormGrades] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Delete confirm state
  const [deleteTarget, setDeleteTarget] = useState<Classroom | null>(null);

  const fetchClasses = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getClassrooms();
      setClassrooms(Array.isArray(data) ? data : []);
    } catch {
      setClassrooms([]);
      setError('No se pudieron cargar las clases. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  // Open modal for creating
  function openCreateModal() {
    setEditingClass(null);
    setFormName('');
    setFormGrades([]);
    setModalOpen(true);
  }

  // Open modal for editing
  function openEditModal(classroom: Classroom) {
    setEditingClass(classroom);
    setFormName(classroom.name);
    setFormGrades([...classroom.grades]);
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditingClass(null);
  }

  function toggleGrade(grade: number) {
    setFormGrades((prev) =>
      prev.includes(grade) ? prev.filter((g) => g !== grade) : [...prev, grade].sort()
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim() || formGrades.length === 0) return;

    setSubmitting(true);
    try {
      if (editingClass) {
        const updateData: ClassroomUpdate = {};
        if (formName.trim() !== editingClass.name) updateData.name = formName.trim();
        if (JSON.stringify(formGrades) !== JSON.stringify(editingClass.grades))
          updateData.grades = formGrades;

        const updated = await updateClassroom(editingClass.id, updateData);
        setClassrooms((prev) =>
          prev.map((c) => (c.id === updated.id ? updated : c))
        );
      } else {
        const newData: ClassroomCreate = {
          name: formName.trim(),
          grades: formGrades,
        };
        const created = await createClassroom(newData);
        setClassrooms((prev) => [...prev, created]);
      }
      closeModal();
    } catch {
      // Keep modal open on error so user can retry
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deleteClassroom(deleteTarget.id);
      setClassrooms((prev) => prev.filter((c) => c.id !== deleteTarget.id));
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
        <div className={styles.loading}>Cargando clases...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorState}>
          <p>{error}</p>
          <button className={styles.retryBtn} onClick={fetchClasses}>
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
        <h2 className={styles.title}>Mis Clases</h2>
        <button
          className={styles.newBtn}
          onClick={openCreateModal}
          aria-label="Crear nueva clase"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          Nueva clase
        </button>
      </div>

      {/* Empty state */}
      {classrooms.length === 0 && (
        <div className={styles.emptyState}>
          <p>Aún no tienes clases creadas.</p>
          <button className={styles.newBtn} onClick={openCreateModal}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Crear tu primera clase
          </button>
        </div>
      )}

      {/* Cards grid */}
      {classrooms.length > 0 && (
        <div className={styles.grid}>
          {classrooms.map((classroom, idx) => (
            <div
              key={classroom.id}
              className={`${styles.card} ${ACCENT_CLASSES[idx % ACCENT_CLASSES.length]}`}
              onClick={() => navigate(`/dashboard/class/${classroom.id}`)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  navigate(`/dashboard/class/${classroom.id}`);
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`Abrir clase ${classroom.name}`}
            >
              {/* Card actions */}
              <div className={styles.cardActions}>
                <button
                  className={styles.iconBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    openEditModal(classroom);
                  }}
                  aria-label={`Editar ${classroom.name}`}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                <button
                  className={styles.iconBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget(classroom);
                  }}
                  aria-label={`Eliminar ${classroom.name}`}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  </svg>
                </button>
              </div>

              {/* Card content */}
              <h3 className={styles.cardName}>{classroom.name}</h3>
              <div className={styles.cardGrades}>
                {classroom.grades.map((g) => (
                  <span key={g} className={styles.gradeBadge}>
                    {g}° grado
                  </span>
                ))}
              </div>
              <div className={styles.cardMeta}>
                <span>0 actividades</span>
                <span>Última actividad: {formatDate(classroom.updated_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {modalOpen && (
        <div
          className={styles.overlay}
          onClick={closeModal}
          role="dialog"
          aria-modal="true"
          aria-label={editingClass ? 'Editar clase' : 'Nueva clase'}
        >
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>
              {editingClass ? 'Editar clase' : 'Nueva clase'}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label htmlFor="class-name">Nombre de la clase</label>
                <input
                  id="class-name"
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Ej: Matemáticas 3° y 4°"
                  autoFocus
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label>Grados</label>
                <div className={styles.gradeOptions} role="group" aria-label="Selección de grados">
                  {AVAILABLE_GRADES.map((grade) => (
                    <button
                      key={grade}
                      type="button"
                      className={`${styles.gradeToggle} ${
                        formGrades.includes(grade) ? styles.gradeToggleActive : ''
                      }`}
                      onClick={() => toggleGrade(grade)}
                      aria-pressed={formGrades.includes(grade)}
                    >
                      {grade}°
                    </button>
                  ))}
                </div>
              </div>

              <div className={styles.modalActions}>
                <button
                  type="button"
                  className={styles.cancelBtn}
                  onClick={closeModal}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={styles.submitBtn}
                  disabled={!formName.trim() || formGrades.length === 0 || submitting}
                >
                  {submitting
                    ? 'Guardando...'
                    : editingClass
                    ? 'Guardar cambios'
                    : 'Crear clase'}
                </button>
              </div>
            </form>
          </div>
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
              ¿Estás seguro de que deseas eliminar la clase{' '}
              <strong>{deleteTarget.name}</strong>? Esta acción no se puede deshacer.
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
