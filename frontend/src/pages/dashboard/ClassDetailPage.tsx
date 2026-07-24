import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Classroom } from '../../types/classroom';
import type { ActivityOutput } from '../../types/activity';
import type { Subject } from '../../types/subject';
import { getClassrooms } from '../../services/classroomService';
import { getSubjects } from '../../services/subjectService';
import { generateActivity, getHistory } from '../../services/activityService';
import styles from './ClassDetailPage.module.css';

export default function ClassDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [classroom, setClassroom] = useState<Classroom | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [history, setHistory] = useState<ActivityOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedActivity, setExpandedActivity] = useState<number | null>(null);
  const [expandedVariants, setExpandedVariants] = useState<Record<string, boolean>>({});
  const [inputValue, setInputValue] = useState('');

  const chatAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load classroom + history
  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [classrooms, historyData, subjectsData] = await Promise.all([
        getClassrooms(),
        getHistory({ class_id: parseInt(id) }),
        getSubjects(),
      ]);
      const found = classrooms.find((c) => c.id === parseInt(id));
      setClassroom(found || null);
      setHistory(Array.isArray(historyData) ? historyData : []);
      setSubjects(Array.isArray(subjectsData) ? subjectsData : []);
    } catch {
      setClassroom(null);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-scroll chat to bottom when new activity is generated
  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [history, generating]);

  // Auto-resize textarea
  function handleTextareaInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInputValue(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }

  // Handle send
  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const topic = inputValue.trim();
    if (!topic || generating || !classroom) return;

    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setGenerating(true);

    try {
      const result = await generateActivity({
        topic,
        classroom_id: classroom.id,
        subject_id: subjects.length > 0 ? subjects[0].id : null,
        grades: classroom.grades,
        subject_name: subjects.length > 0 ? subjects[0].name : '',
        available_resources: null,
      });
      setHistory((prev) => [result, ...prev]);
      setExpandedActivity(result.id);
    } catch {
      // Error handled silently - user can retry
    } finally {
      setGenerating(false);
    }
  }

  // Handle keyboard submit
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e as unknown as React.FormEvent);
    }
  }

  // Toggle variant collapse
  function toggleVariant(activityId: number | null, grade: number) {
    const key = `${activityId}-${grade}`;
    setExpandedVariants((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  // Format date
  function formatDate(dateStr: string | null) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function formatDateShort(dateStr: string | null) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
    });
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>Cargando clase...</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Main panel */}
      <div className={styles.mainPanel}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <button
              className={styles.backBtn}
              onClick={() => navigate('/dashboard/classes')}
              aria-label="Volver a clases"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <h2 className={styles.className}>
              {classroom ? classroom.name : `Clase #${id}`}
            </h2>
          </div>
          {classroom && classroom.grades.length > 0 && (
            <div className={styles.classMeta}>
              {classroom.grades.map((g) => (
                <span key={g} className={styles.gradeBadge}>{g}° grado</span>
              ))}
            </div>
          )}
        </div>

        {/* Chat area */}
        <div className={styles.chatArea} ref={chatAreaRef}>
          {/* Empty state */}
          {history.length === 0 && !generating && (
            <div className={styles.emptyChat}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <p>
                Escribe un tema o instrucción para generar una actividad diferenciada para esta clase.
              </p>
            </div>
          )}

          {/* Thinking indicator */}
          {generating && (
            <div className={styles.thinkingIndicator}>
              <div className={styles.dots}>
                <span className={styles.dot} />
                <span className={styles.dot} />
                <span className={styles.dot} />
              </div>
              <span className={styles.thinkingText}>Generando actividad...</span>
            </div>
          )}

          {/* Activity history - expanded view */}
          {history.map((activity) => {
            const isExpanded = expandedActivity === activity.id;
            return (
              <div key={activity.id ?? activity.topic + activity.created_at}>
                {isExpanded ? (
                  <ActivityCard
                    activity={activity}
                    expandedVariants={expandedVariants}
                    onToggleVariant={toggleVariant}
                    formatDate={formatDate}
                    onCollapse={() => setExpandedActivity(null)}
                  />
                ) : (
                  <div
                    className={styles.historyItem}
                    onClick={() => setExpandedActivity(activity.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setExpandedActivity(activity.id);
                      }
                    }}
                    aria-label={`Ver actividad: ${activity.topic}`}
                  >
                    <div className={styles.historyItemHeader}>
                      <span className={styles.historyItemTopic}>{activity.topic}</span>
                      <span className={styles.historyItemDate}>
                        {formatDateShort(activity.created_at)}
                      </span>
                    </div>
                    <div className={styles.historyItemMeta}>
                      {activity.subject_name && <span>{activity.subject_name}</span>}
                      {activity.variants.length > 0 && (
                        <span> · {activity.variants.length} variante{activity.variants.length > 1 ? 's' : ''}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Chat input */}
        <div className={styles.chatInputArea}>
          <form className={styles.chatForm} onSubmit={handleSend}>
            <textarea
              ref={textareaRef}
              className={styles.chatInput}
              placeholder="Escribe un tema para generar actividad..."
              value={inputValue}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={generating}
              aria-label="Tema o instrucción para generar actividad"
            />
            <button
              type="submit"
              className={styles.sendBtn}
              disabled={!inputValue.trim() || generating}
              aria-label="Enviar"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </form>
        </div>
      </div>

      {/* Right sidebar - Multimedia */}
      <aside className={styles.sidePanel}>
        <h3 className={styles.sidePanelTitle}>Contenido multimedia</h3>

        <div className={styles.mediaGrid}>
          {/* Placeholder thumbnails */}
          <MediaThumbnail label="Guía docente" type="pdf" />
          <MediaThumbnail label="Fichas grado 3" type="doc" />
          <MediaThumbnail label="Imágenes tema" type="image" />
          <MediaThumbnail label="Rúbrica eval." type="pdf" />
        </div>

        <button className={styles.uploadBtn} aria-label="Subir archivo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Subir archivo
        </button>

        <p className={styles.mediaEmpty}>
          Los archivos subidos se asociarán a esta clase y podrán usarse como recurso para la generación.
        </p>
      </aside>
    </div>
  );
}

/* --- Sub-components --- */

interface ActivityCardProps {
  activity: ActivityOutput;
  expandedVariants: Record<string, boolean>;
  onToggleVariant: (activityId: number | null, grade: number) => void;
  formatDate: (date: string | null) => string;
  onCollapse: () => void;
}

function ActivityCard({
  activity,
  expandedVariants,
  onToggleVariant,
  formatDate,
  onCollapse,
}: ActivityCardProps) {
  return (
    <div className={styles.activityCard}>
      <div className={styles.activityCardHeader}>
        <span className={styles.activityTopic}>{activity.topic}</span>
        <span className={styles.activityDate}>{formatDate(activity.created_at)}</span>
      </div>

      {activity.subject_name && (
        <div className={styles.activitySubject}>{activity.subject_name}</div>
      )}

      {/* Anchor activity */}
      <div className={styles.anchorSection}>
        <div className={styles.anchorLabel}>Actividad ancla</div>
        <div className={styles.anchorContent}>{activity.anchor_activity}</div>
      </div>

      {/* Variants per grade - collapsible */}
      {activity.variants.length > 0 && (
        <div className={styles.variantsSection}>
          <div className={styles.variantsTitle}>
            Variantes por grado ({activity.variants.length})
          </div>
          {activity.variants.map((variant) => {
            const key = `${activity.id}-${variant.grade}`;
            const isOpen = expandedVariants[key] ?? false;
            return (
              <div key={variant.grade} className={styles.variantItem}>
                <button
                  className={styles.variantHeader}
                  onClick={() => onToggleVariant(activity.id, variant.grade)}
                  aria-expanded={isOpen}
                  aria-controls={`variant-${key}`}
                >
                  <span className={styles.variantGrade}>
                    <span className={styles.variantGradeBadge}>{variant.grade}°</span>
                    Grado {variant.grade}
                  </span>
                  <svg
                    className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
                {isOpen && (
                  <div id={`variant-${key}`} className={styles.variantBody}>
                    <div className={styles.variantField}>
                      <div className={styles.variantFieldLabel}>Contenido</div>
                      <div className={styles.variantFieldContent}>{variant.content}</div>
                    </div>
                    <div className={styles.variantField}>
                      <div className={styles.variantFieldLabel}>Instrucciones</div>
                      <div className={styles.variantFieldContent}>{variant.instructions}</div>
                    </div>
                    <div className={styles.variantField}>
                      <div className={styles.variantFieldLabel}>Ejercicios</div>
                      <div className={styles.variantFieldContent}>{variant.exercises}</div>
                    </div>
                    {variant.aligned_standards.length > 0 && (
                      <div className={styles.variantField}>
                        <div className={styles.variantFieldLabel}>Estándares alineados</div>
                        <div className={styles.standardsList}>
                          {variant.aligned_standards.map((std, i) => (
                            <span key={i} className={styles.standardBadge}>
                              {std.country} · {std.subject} · Grado {std.grade}: {std.text}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Collapse button */}
      <button
        className={styles.backBtn}
        onClick={onCollapse}
        style={{ marginTop: '12px' }}
        aria-label="Colapsar actividad"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 15l-6-6-6 6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  );
}

/* Media thumbnail sub-component */
interface MediaThumbnailProps {
  label: string;
  type: 'pdf' | 'doc' | 'image';
}

function MediaThumbnail({ label, type }: MediaThumbnailProps) {
  const icons: Record<string, JSX.Element> = {
    pdf: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    doc: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2v6h6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    image: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="M21 15l-5-5L5 21" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  };

  return (
    <div className={styles.mediaThumbnail} role="button" tabIndex={0} aria-label={label}>
      {icons[type]}
      <span className={styles.mediaThumbnailLabel}>{label}</span>
    </div>
  );
}
