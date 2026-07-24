import { useEffect, useState, useCallback, useRef } from 'react';
import type { ActivityOutput } from '../../types/activity';
import type { Classroom } from '../../types/classroom';
import type { Subject } from '../../types/subject';
import { getHistory, deleteActivity } from '../../services/activityService';
import { getClassrooms } from '../../services/classroomService';
import { getSubjects } from '../../services/subjectService';
import styles from './HistoryPage.module.css';

export default function HistoryPage() {
  const [activities, setActivities] = useState<ActivityOutput[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSubject, setFilterSubject] = useState<number | ''>('');
  const [filterClass, setFilterClass] = useState<number | ''>('');

  // Detail modal
  const [detailActivity, setDetailActivity] = useState<ActivityOutput | null>(null);
  const [expandedVariants, setExpandedVariants] = useState<Set<number>>(new Set());

  // Delete confirm
  const [deleteTarget, setDeleteTarget] = useState<ActivityOutput | null>(null);

  // Debounce ref
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchHistory = useCallback(async (params?: { subject_id?: number; class_id?: number; search?: string }) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getHistory(params);
      setActivities(Array.isArray(data) ? data : []);
    } catch {
      setActivities([]);
      setError('No se pudo cargar el historial. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFilters = useCallback(async () => {
    try {
      const [classData, subjectData] = await Promise.all([
        getClassrooms(),
        getSubjects(),
      ]);
      setClassrooms(Array.isArray(classData) ? classData : []);
      setSubjects(Array.isArray(subjectData) ? subjectData : []);
    } catch {
      // Non-critical: filters won't populate but history still works
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    fetchFilters();
  }, [fetchHistory, fetchFilters]);

  // Build params and fetch when filters change
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      const params: { subject_id?: number; class_id?: number; search?: string } = {};
      if (filterSubject !== '') params.subject_id = filterSubject;
      if (filterClass !== '') params.class_id = filterClass;
      if (searchTerm.trim()) params.search = searchTerm.trim();
      fetchHistory(params);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [searchTerm, filterSubject, filterClass, fetchHistory]);

  async function handleDelete() {
    if (!deleteTarget || deleteTarget.id === null) return;
    try {
      await deleteActivity(deleteTarget.id);
      setActivities((prev) => prev.filter((a) => a.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setDeleteTarget(null);
    }
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  function openDetail(activity: ActivityOutput) {
    setDetailActivity(activity);
    setExpandedVariants(new Set());
  }

  function closeDetail() {
    setDetailActivity(null);
  }

  function toggleVariant(grade: number) {
    setExpandedVariants((prev) => {
      const next = new Set(prev);
      if (next.has(grade)) {
        next.delete(grade);
      } else {
        next.add(grade);
      }
      return next;
    });
  }

  // Render loading state
  if (loading && activities.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>Cargando historial...</div>
      </div>
    );
  }

  // Render error state
  if (error && activities.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.errorState}>
          <p>{error}</p>
          <button className={styles.retryBtn} onClick={() => fetchHistory()}>
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
        <h2 className={styles.title}>Historial</h2>
      </div>

      {/* Toolbar: search + filters */}
      <div className={styles.toolbar}>
        <div className={styles.searchWrapper}>
          <svg
            className={styles.searchIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Buscar por tema o palabra clave..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Buscar actividades"
          />
        </div>

        <select
          className={styles.filterSelect}
          value={filterSubject}
          onChange={(e) => setFilterSubject(e.target.value ? Number(e.target.value) : '')}
          aria-label="Filtrar por materia"
        >
          <option value="">Todas las materias</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        <select
          className={styles.filterSelect}
          value={filterClass}
          onChange={(e) => setFilterClass(e.target.value ? Number(e.target.value) : '')}
          aria-label="Filtrar por clase"
        >
          <option value="">Todas las clases</option>
          {classrooms.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Empty state */}
      {activities.length === 0 && !loading && (
        <div className={styles.emptyState}>
          <p>No se encontraron actividades.</p>
          {(searchTerm || filterSubject || filterClass) && (
            <p>Intenta ajustar los filtros de búsqueda.</p>
          )}
        </div>
      )}

      {/* Activity list */}
      {activities.length > 0 && (
        <div className={styles.list} role="list">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className={styles.listItem}
              onClick={() => openDetail(activity)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  openDetail(activity);
                }
              }}
              tabIndex={0}
              role="listitem"
              aria-label={`Actividad: ${activity.topic}`}
            >
              <div className={styles.itemContent}>
                <h3 className={styles.itemTopic}>{activity.topic}</h3>
                <div className={styles.itemMeta}>
                  {activity.subject_name && (
                    <span className={styles.metaBadge}>{activity.subject_name}</span>
                  )}
                  {activity.classroom_name && (
                    <span className={styles.metaBadge}>{activity.classroom_name}</span>
                  )}
                  {activity.created_at && (
                    <span className={styles.metaDate}>{formatDate(activity.created_at)}</span>
                  )}
                </div>
              </div>

              <div className={styles.itemActions}>
                <button
                  className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget(activity);
                  }}
                  aria-label={`Eliminar actividad: ${activity.topic}`}
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

      {/* Detail Modal */}
      {detailActivity && (
        <div
          className={styles.overlay}
          onClick={closeDetail}
          role="dialog"
          aria-modal="true"
          aria-label={`Detalle de actividad: ${detailActivity.topic}`}
        >
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>{detailActivity.topic}</h3>
              <button
                className={styles.closeBtn}
                onClick={closeDetail}
                aria-label="Cerrar detalle"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            <div className={styles.modalMeta}>
              {detailActivity.subject_name && (
                <span className={styles.metaBadge}>{detailActivity.subject_name}</span>
              )}
              {detailActivity.classroom_name && (
                <span className={styles.metaBadge}>{detailActivity.classroom_name}</span>
              )}
              {detailActivity.created_at && (
                <span className={styles.metaDate}>{formatDate(detailActivity.created_at)}</span>
              )}
            </div>

            {/* Anchor activity */}
            <div className={styles.modalSection}>
              <h4 className={styles.modalSectionTitle}>Actividad ancla</h4>
              <p className={styles.modalText}>{detailActivity.anchor_activity}</p>
            </div>

            {/* Variants by grade */}
            {detailActivity.variants.length > 0 && (
              <div className={styles.modalSection}>
                <h4 className={styles.modalSectionTitle}>Variantes por grado</h4>
                {detailActivity.variants.map((variant) => (
                  <div key={variant.grade}>
                    <button
                      className={styles.variantToggle}
                      onClick={() => toggleVariant(variant.grade)}
                      aria-expanded={expandedVariants.has(variant.grade)}
                    >
                      <svg
                        className={`${styles.variantToggleIcon} ${
                          expandedVariants.has(variant.grade) ? styles.variantToggleOpen : ''
                        }`}
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      {variant.grade}° grado
                    </button>
                    {expandedVariants.has(variant.grade) && (
                      <div className={styles.variantContent}>
                        {variant.content && (
                          <>
                            <strong>Contenido:</strong>
                            {'\n'}
                            {variant.content}
                            {'\n\n'}
                          </>
                        )}
                        {variant.instructions && (
                          <>
                            <strong>Instrucciones:</strong>
                            {'\n'}
                            {variant.instructions}
                            {'\n\n'}
                          </>
                        )}
                        {variant.exercises && (
                          <>
                            <strong>Ejercicios:</strong>
                            {'\n'}
                            {variant.exercises}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
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
              ¿Estás seguro de que deseas eliminar la actividad{' '}
              <strong>{deleteTarget.topic}</strong>? Esta acción no se puede deshacer.
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
