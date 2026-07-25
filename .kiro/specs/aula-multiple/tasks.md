# Implementation Plan: Aula Múltiple

## Overview

Implementación incremental del sistema Aula Múltiple siguiendo el orden: configuración base (Docker, entorno, variables) → frontend (estructura, features, componentes) → backend (estructura, endpoints, agente, RAG, datos). Cada tarea es un paso ejecutable pequeño que construye sobre el anterior.

## Tasks

- [x] 1. Configuración base del proyecto
  - [x] 1.1 Crear estructura raíz del proyecto y archivos de configuración Docker
    - Crear `docker-compose.yml` con servicios `backend` y `db` (pgvector/pgvector:pg16)
    - Crear `backend/Dockerfile` con imagen Python 3.11, instalación de dependencias
    - Crear `.env.example` con todas las variables: DATABASE_URL, LLM_API_KEY, LLM_PROVIDER, EMBEDDING_API_KEY, JWT_SECRET, JWT_EXPIRATION_MINUTES, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    - Crear `.gitignore` para Python, Node, Docker, .env
    - _Requisitos: 9.1, 9.2, 9.3, 9.4_

  - [x] 1.2 Configurar entorno Conda y dependencias Python del backend
    - Crear `backend/environment.yml` (Conda) con Python 3.11 y dependencias core
    - Crear `backend/requirements.txt` con: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, python-jose[cryptography], passlib[bcrypt], langgraph, langchain-core, pgvector, httpx, pdfplumber, hypothesis, pytest, pytest-asyncio
    - _Requisitos: 9.1_

  - [x] 1.3 Configurar módulo de settings con pydantic-settings
    - Crear `backend/app/__init__.py`
    - Crear `backend/app/config.py` con clase Settings que lea variables de entorno: DATABASE_URL, LLM_API_KEY, LLM_PROVIDER, EMBEDDING_API_KEY, JWT_SECRET, JWT_EXPIRATION_MINUTES, LLM_TIMEOUT_SECONDS (default 60)
    - _Requisitos: 9.4, 8.5_

  - [x] 1.4 Configurar Alembic y migración inicial de esquema
    - Inicializar Alembic en `backend/alembic/`
    - Configurar `alembic.ini` para usar DATABASE_URL del entorno
    - Crear migración inicial con extensión pgvector y todas las tablas: users, classrooms, subjects, activities, activity_variants, variant_standards, curriculum_embeddings
    - _Requisitos: 9.3_

- [x] 2. Checkpoint - Verificar configuración base
  - Ejecutar `docker compose up` y confirmar que los contenedores backend y db se levantan correctamente, las migraciones se aplican y pgvector está habilitado. Preguntar al usuario si surgen dudas.

- [x] 3. Frontend — Estructura y configuración inicial
  - [x] 3.1 Inicializar proyecto React + TypeScript con Vite
    - Crear proyecto en `frontend/` con Vite + React + TypeScript
    - Instalar dependencias: react-router-dom, axios
    - Usar CSS Modules para estilos (soporte nativo de Vite, sin configuración extra)
    - Crear `frontend/Dockerfile` para build de producción con nginx
    - _Requisitos: 6.5_

  - [x] 3.2 Definir tipos TypeScript del dominio
    - Crear `frontend/src/types/activity.ts`: interfaces ActivityOutput, VariantOutput, CurriculumStandard, GenerateRequest
    - Crear `frontend/src/types/classroom.ts`: interfaces Classroom, ClassroomCreate, ClassroomUpdate
    - Crear `frontend/src/types/subject.ts`: interfaces Subject, SubjectCreate
    - Crear `frontend/src/types/auth.ts`: interfaces LoginRequest, RegisterRequest, TokenResponse, User
    - _Requisitos: 6.1, 6.3_

  - [x] 3.3 Crear servicios API (capa de comunicación con backend)
    - Crear `frontend/src/services/api.ts`: instancia axios con baseURL, interceptor para JWT, manejo de errores
    - Crear `frontend/src/services/authService.ts`: login, register, logout
    - Crear `frontend/src/services/activityService.ts`: generateActivity, getHistory, getActivity, deleteActivity, searchHistory
    - Crear `frontend/src/services/classroomService.ts`: CRUD de clases
    - Crear `frontend/src/services/subjectService.ts`: CRUD de materias
    - _Requisitos: 6.1, 8.1_

  - [x] 3.4 Implementar layout principal, navegación y design system
    - Configurar design system: paletas light (crema, verde, púrpura, naranja, azul) y dark (negro, magenta, cyan, rosa, amarillo)
    - Agregar Google Fonts: Cause (headings) + Readex Pro (body) en index.html
    - Crear `frontend/src/components/common/Navbar.tsx`: navbar público sticky con glassmorphism, logo placeholder, anclas a secciones del homepage, botones Iniciar sesión / Registrarse / Dashboard
    - Crear `frontend/src/components/Layout/DashboardLayout.tsx`: layout full-viewport con sidebar + área principal (Outlet)
    - Crear `frontend/src/components/Layout/Sidebar.tsx`: sidebar oscuro estilo Claude con username, botón "+ Nueva clase", nav con SVG icons (Generar, Historial, Clases, Materias), sección "Mis Clases", sección "Contenido multimedia", botón collapse
    - Crear `frontend/src/components/common/ProtectedRoute.tsx`: verifica token en localStorage, redirige a /login
    - Crear `frontend/src/pages/HomePage.tsx`: homepage con 6 secciones (Hero, Características, Cómo funciona, CTA final, Footer) con placeholders para ilustraciones
    - Configurar React Router: / (home), /login, /register, /dashboard/* (protegido)
    - Diseño responsivo mobile-first (min 320px)
    - _Requisitos: 6.4, 6.5_

  - [x] 3.5 Implementar páginas de autenticación (Login/Registro)
    - Crear `frontend/src/pages/LoginPage.tsx` con formulario email + contraseña, card centrado con design system (Cause para título, Readex Pro para campos)
    - Crear `frontend/src/pages/RegisterPage.tsx` con formulario nombre + email + contraseña
    - Crear hook `frontend/src/hooks/useAuth.ts` para gestión del token JWT en localStorage, estado de loading, errores
    - Implementar redirección post-login a /dashboard/classes
    - Estilos: inputs con border-radius 12px, botón submit primario pill, link a la otra página de auth
    - _Requisitos: 7.1, 7.2_

  - [x] 3.6 Implementar vista de Clases (cards tipo Projects de Claude)
    - Crear `frontend/src/pages/dashboard/ClassesPage.tsx`: grid de cards tipo "Projects" de Claude
    - Cada card muestra: nombre de clase, grados, número de actividades, fecha última actividad
    - Botón "Nueva clase" abre modal/formulario inline (nombre + selección de grados 2-6 + materia asociada)
    - Cards con border-radius 16px, sombra suave, acento de color por clase
    - Implementar edición y eliminación con confirmación
    - Hacer clic en un card navega a `/dashboard/class/:id`
    - _Requisitos: 5.1, 5.3, 5.4, 5.5, 6.1_

  - [x] 3.7 Implementar vista de Clase individual (chat + panel lateral)
    - Crear `frontend/src/pages/dashboard/ClassDetailPage.tsx`: layout tipo "Perfil profesional" de Claude
    - Panel central: historial de actividades generadas para esta clase (lista con título + fecha, tipo "Recents" de Claude)
    - Input de chat en la parte inferior (estilo Claude): el docente escribe tema/instrucción y envía para generar
    - Indicador de "thinking/typing" mientras el agente procesa (dots animados)
    - Resultado de generación como burbuja/card con formato rico: actividad ancla + variantes colapsables por grado
    - Panel lateral derecho: sección "Contenido multimedia" con thumbnails de documentos/archivos asociados a la clase
    - _Requisitos: 6.1, 6.2, 6.3, 4.2, 4.4_

  - [x] 3.8 Implementar página de Historial global
    - Crear `frontend/src/pages/dashboard/HistoryPage.tsx`: lista de todas las actividades del docente ordenadas por fecha desc
    - Implementar filtros por materia y clase (selectores en top bar)
    - Implementar búsqueda por palabra clave (input con ícono search)
    - Cada item muestra: tema, clase, materia, fecha
    - Clic en item navega a la actividad dentro de su clase o abre modal de detalle
    - Implementar eliminación con confirmación
    - _Requisitos: 4.2, 4.3, 4.4, 4.5_

  - [x] 3.9 Implementar página de Materias
    - Crear `frontend/src/pages/dashboard/SubjectsPage.tsx`: lista de materias del docente
    - Formulario inline para crear nueva materia (nombre)
    - Eliminar con confirmación
    - Diseño con cards o lista simple acorde al design system
    - _Requisitos: 5.2, 5.5_

  - [x] 3.10 Implementar detección offline y manejo de errores en UI
    - Crear componente `OfflineBanner.tsx` que detecte pérdida de conexión y muestre mensaje informativo
    - Implementar manejo de errores HTTP globales (401 → logout, 422 → mostrar errores de campo, 504 → mensaje timeout IA)
    - _Requisitos: 6.6, 8.2, 8.5_

- [x] 4. Checkpoint - Verificar frontend
  - Verificar que el frontend compila sin errores, las rutas navegan correctamente y los componentes renderizan. Preguntar al usuario si surgen dudas.

- [x] 5. Backend — Modelos de datos y módulo de autenticación
  - [x] 5.1 Crear modelos SQLAlchemy
    - Crear `backend/app/models/base.py` con Base declarativa
    - Crear `backend/app/models/user.py`: User (id, email, password_hash, name, created_at, updated_at)
    - Crear `backend/app/models/classroom.py`: Classroom (id, user_id FK, name, grades ARRAY, timestamps)
    - Crear `backend/app/models/subject.py`: Subject (id, user_id FK, name, created_at)
    - Crear `backend/app/models/activity.py`: Activity, ActivityVariant, VariantStandard con relaciones y cascade delete
    - Crear `backend/app/models/curriculum_embedding.py`: CurriculumEmbedding con Vector(1536) y content_hash
    - _Requisitos: 3.1, 4.1, 5.1, 5.2, 10.3_

  - [x] 5.2 Crear schemas Pydantic de request/response
    - Crear `backend/app/schemas/auth.py`: RegisterRequest (email regex, password min 8), LoginRequest, TokenResponse, UserResponse
    - Crear `backend/app/schemas/activity.py`: GenerateRequest (validador grados 2-6, rango 1-12, sin duplicados), CurriculumStandard, VariantOutput, ActivityOutput
    - Crear `backend/app/schemas/classroom.py`: ClassroomCreate (validador grados), ClassroomUpdate, ClassroomResponse
    - Crear `backend/app/schemas/subject.py`: SubjectCreate, SubjectResponse
    - Crear `backend/app/schemas/history.py`: HistorySummary
    - _Requisitos: 8.2, 8.3, 5.1_

  - [x]* 5.3 Escribir test de propiedad para validación de grados
    - **Propiedad 11: Validación de rango de grados**
    - **Valida: Requisitos 5.1, 8.3**

  - [ ] 5.4 Escribir test de propiedad para validación de entrada 422
    - **Propiedad 17: Validación de entrada retorna 422**
    - **Valida: Requisitos 8.2**

  - [x] 5.5 Implementar módulo de autenticación
    - Crear `backend/app/auth/security.py`: hash_password (bcrypt), verify_password
    - Crear `backend/app/auth/jwt.py`: create_access_token (JWT con user_id + exp), verify_token (lanza 401 si inválido/expirado)
    - Crear `backend/app/dependencies.py`: get_db (async session), get_current_user (extrae user de JWT)
    - _Requisitos: 7.1, 7.2, 7.3, 7.4_

  - [x]* 5.6 Escribir tests de propiedad para autenticación
    - **Propiedad 14: Contraseña almacenada como hash**
    - **Propiedad 15: Token JWT válido tras login exitoso**
    - **Propiedad 16: Rechazo de tokens inválidos**
    - **Valida: Requisitos 7.1, 7.2, 7.3**

  - [x] 5.7 Implementar endpoints de autenticación
    - Crear `backend/app/api/auth.py`: POST /auth/register (crea usuario con password hasheada, 201), POST /auth/login (valida credenciales, emite JWT)
    - Crear `backend/app/crud/users.py`: create_user, get_user_by_email
    - _Requisitos: 7.1, 7.2, 8.1_

- [x] 6. Backend — CRUD de Clases y Materias
  - [x] 6.1 Implementar CRUD y endpoints de Clases
    - Crear `backend/app/crud/classes.py`: create_class, get_classes_by_user, update_class, delete_class
    - Crear `backend/app/api/classes.py`: POST /classes (valida 2-6 grados), GET /classes, PUT /classes/{id}, DELETE /classes/{id} (conserva historial)
    - Implementar que la eliminación de clase ponga classroom_id=null en actividades asociadas (preserva datos denormalizados)
    - _Requisitos: 5.1, 5.4, 5.5, 8.1_

  - [x] 6.2 Implementar CRUD y endpoints de Materias
    - Crear `backend/app/crud/subjects.py`: create_subject, get_subjects_by_user, delete_subject
    - Crear `backend/app/api/subjects.py`: POST /subjects, GET /subjects, DELETE /subjects/{id} (conserva historial poniendo subject_id=null)
    - _Requisitos: 5.2, 5.5, 8.1_

  - [x]* 6.3 Escribir test de propiedad para preservación del historial ante cambios
    - **Propiedad 12: Preservación del historial ante cambios de entidades**
    - **Valida: Requisitos 5.4, 5.5**

  - [x]* 6.4 Escribir test de propiedad para aislamiento de datos entre docentes
    - **Propiedad 13: Aislamiento de datos entre docentes**
    - **Valida: Requisitos 7.4, 5.2**

- [x] 7. Backend — Historial de actividades
  - [x] 7.1 Implementar CRUD y endpoints de Historial
    - Crear `backend/app/crud/history.py`: save_activity, list_history (filtros materia/clase, orden fecha desc), get_activity_by_id, search_history (keyword en tema/contenido), delete_activity
    - Crear `backend/app/api/history.py`: GET /history (filtros + búsqueda), GET /history/{id}, DELETE /history/{id}
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 8.1_

  - [x]* 7.2 Escribir tests de propiedad para historial
    - **Propiedad 7: Round-trip de persistencia de actividades**
    - **Propiedad 8: Ordenamiento del historial por fecha**
    - **Propiedad 9: Búsqueda por keyword en historial**
    - **Propiedad 10: Eliminación permanente de actividades**
    - **Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 8. Checkpoint - Verificar backend CRUD y autenticación
  - Ejecutar tests unitarios y de propiedad del backend. Verificar que los endpoints de auth, clases, materias e historial funcionan correctamente. Preguntar al usuario si surgen dudas.

- [x] 9. Backend — Módulo RAG Curricular
  - [x] 9.1 Implementar servicio de embeddings
    - Crear `backend/app/rag/embeddings.py`: clase EmbeddingService con métodos generate(text) y generate_batch(texts) usando API externa (configurable vía EMBEDDING_API_KEY)
    - _Requisitos: 3.1, 10.2_

  - [x] 9.2 Implementar retriever de estándares curriculares
    - Crear `backend/app/rag/retriever.py`: clase CurriculumRetriever con método search(query, grades, subject, country, top_k=5, similarity_threshold=0.7)
    - Implementar búsqueda por cosine similarity en pgvector filtrando por grado y materia
    - Retornar lista vacía si ningún resultado supera el umbral
    - Cada resultado incluye: país, grado, materia, texto, score
    - _Requisitos: 3.1, 3.2, 3.3, 3.4_

  - [x] 9.3 Escribir tests de propiedad para RAG
    - **Propiedad 4: Corrección de filtros y completitud de resultados RAG**
    - **Propiedad 5: Comportamiento bajo umbral de similitud**
    - **Valida: Requisitos 1.3, 3.2, 3.3, 3.4**

- [x] 10. Backend — MCP Server y Agente LangGraph
  - [x] 10.1 Implementar MCP Server embebido
    - Crear `backend/app/mcp_server/server.py`: definir servidor MCP "aula-multiple-curriculum"
    - Crear `backend/app/mcp_server/tools.py`: herramienta `consultar_estandares(query, grades, subject, country, top_k)` que invoca CurriculumRetriever
    - _Requisitos: 2.2_

  - [x] 10.2 Definir estado del grafo y estructura del agente
    - Crear `backend/app/agent/state.py`: TypedDict AgentState con campos de entrada, outputs por nodo, current_node y error
    - Crear `backend/app/agent/graph.py`: build_activity_graph() con StateGraph de 4 nodos secuenciales conectados linealmente al END
    - _Requisitos: 2.1_

  - [x] 10.3 Implementar nodo 1: Análisis Curricular
    - Crear `backend/app/agent/nodes/curriculum_analysis.py`: invoca herramienta MCP consultar_estandares con topic, grades, subject
    - Manejo de errores: captura excepciones, registra en state.error con nombre de nodo
    - Crear prompt en `backend/app/agent/prompts/curriculum_analysis.txt`
    - _Requisitos: 2.1, 2.2, 2.6, 1.3_

  - [x] 10.4 Implementar nodo 2: Diseño de Actividad
    - Crear `backend/app/agent/nodes/activity_design.py`: genera actividad ancla + variantes por grado usando LLM con contexto curricular
    - Implementar timeout de 60s hacia API LLM (asyncio.timeout)
    - Crear prompt en `backend/app/agent/prompts/activity_design.txt`
    - _Requisitos: 2.1, 2.3, 1.1, 1.2, 1.4, 8.5_

  - [x] 10.5 Implementar nodo 3: Adaptación de Recursos
    - Crear `backend/app/agent/nodes/resource_adaptation.py`: adapta instrucciones según recursos disponibles; si no hay recursos, asume básicos (pizarra, cuadernos, lápices)
    - Crear prompt en `backend/app/agent/prompts/resource_adaptation.txt`
    - _Requisitos: 2.1, 2.4, 1.5, 1.6_

  - [x] 10.6 Implementar nodo 4: Formateo de Salida
    - Crear `backend/app/agent/nodes/output_formatting.py`: estructura la salida final en JSON validado con Pydantic (ActivityOutput)
    - Separar campos: anchor_activity, variantes por grado con estándares alineados
    - _Requisitos: 2.1, 2.5_

  - [x] 10.7 Escribir tests de propiedad para el grafo del agente
    - **Propiedad 1: Invariante estructural de salida**
    - **Propiedad 2: Orden secuencial de ejecución de nodos**
    - **Propiedad 3: Identificación de nodo en errores**
    - **Propiedad 6: Alineación variante-estándar**
    - **Valida: Requisitos 1.1, 2.1, 2.5, 2.6, 1.4**

- [x] 11. Backend — Endpoint de generación de actividades
  - [x] 11.1 Implementar endpoint POST /activities/generate
    - Crear `backend/app/api/activities.py`: valida input (2-6 grados), invoca grafo LangGraph, persiste resultado en historial, retorna ActivityOutput
    - Implementar timeout global de 60s hacia servicio LLM con respuesta 504
    - _Requisitos: 1.1, 8.1, 8.3, 8.5_

  - [x] 11.2 Crear router principal y montar la app FastAPI
    - Crear `backend/app/api/router.py`: monta todos los sub-routers bajo prefijo /api/v1
    - Crear `backend/app/main.py`: FastAPI app factory con CORS, include router, documentación OpenAPI automática
    - _Requisitos: 8.1, 8.4_

- [x] 12. Checkpoint - Verificar agente y endpoint de generación
  - Ejecutar tests del módulo agente. Verificar flujo completo: solicitud → grafo 4 nodos → respuesta JSON. Preguntar al usuario si surgen dudas.

- [ ] 13. Script de ingesta de estándares curriculares
  - [x] 13.1 Implementar script de ingesta offline
    - Crear `backend/scripts/ingest_curriculum.py`: CLI independiente que procesa PDFs curriculares
    - Implementar: extracción de texto (pdfplumber), chunking (500 chars, overlap 50), generación de embeddings (batch), deduplicación por content_hash (SHA-256), inserción en pgvector con metadatos (país, grado, materia)
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x]* 13.2 Escribir tests de propiedad para ingesta
    - **Propiedad 18: Chunking produce fragmentos válidos**
    - **Propiedad 19: Persistencia de embeddings con metadatos**
    - **Propiedad 20: Idempotencia de ingesta**
    - **Valida: Requisitos 10.2, 10.3, 10.5**

- [x] 14. Integración final y wiring
  - [x] 14.1 Conectar frontend con backend (ajustes de integración)
    - Verificar que las URLs del frontend apuntan al backend correctamente
    - Configurar CORS en FastAPI para permitir requests del frontend
    - Ajustar docker-compose.yml para incluir servicio frontend con build y port mapping
    - Verificar flujo completo: registro → login → crear clase/materia → generar actividad → ver historial
    - _Requisitos: 6.1, 6.2, 6.3, 9.3_

  - [x] 14.2 Escribir tests de integración end-to-end
    - Test flujo completo: registro → login → crear clase → generar actividad → consultar historial → eliminar
    - Test docker compose up levanta todos los servicios
    - _Requisitos: 9.3, 8.1_

- [ ] 15. Checkpoint final - Validar sistema completo
  - Ejecutar todos los tests (unitarios, propiedad, integración). Verificar que docker compose up levanta el sistema completo funcional. Preguntar al usuario si surgen dudas.

## Notes

- Las tareas marcadas con `*` son opcionales (tests de propiedad) y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental antes de avanzar al siguiente módulo
- El orden de implementación sigue la prioridad del usuario: configuración base → frontend → backend
- Los tests de propiedad validan propiedades universales de corrección definidas en el diseño
- Los tests unitarios validan ejemplos específicos y casos edge
- El frontend se desarrolla primero para tener UI funcional que luego se conecta al backend
- El backend se construye módulo a módulo: modelos → auth → CRUD → RAG → agente → integración
- **Design System**: Paleta light (crema #F5F2EB, verde #2BAB6F, púrpura #7B5EA7, naranja #F07C4D), dark (negro #0F0F14, magenta #FF4D9B, cyan #3ECFC0). Fuentes: Cause (headings/juguetona) + Readex Pro (body). Cards 16px radius, sombras suaves.
- **UI Pattern**: Dashboard con sidebar oscuro estilo Claude/ChatGPT. Clases = Projects. Chat puro para generación. Panel multimedia lateral.
- **Ilustraciones**: Se integrarán en una fase posterior; las tareas dejan placeholders descriptivos.
- La ruta `/dashboard/class/:id` es la vista individual de clase con chat + panel multimedia

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4"] },
    { "id": 3, "tasks": ["3.1"] },
    { "id": 4, "tasks": ["3.2", "3.3"] },
    { "id": 5, "tasks": ["3.4", "3.5"] },
    { "id": 6, "tasks": ["3.6", "3.8", "3.9"] },
    { "id": 7, "tasks": ["3.7"] },
    { "id": 8, "tasks": ["3.10"] },
    { "id": 9, "tasks": ["5.1"] },
    { "id": 10, "tasks": ["5.2", "5.5"] },
    { "id": 11, "tasks": ["5.3", "5.4", "5.6", "5.7"] },
    { "id": 12, "tasks": ["6.1", "6.2"] },
    { "id": 13, "tasks": ["6.3", "6.4", "7.1"] },
    { "id": 14, "tasks": ["7.2"] },
    { "id": 15, "tasks": ["9.1"] },
    { "id": 16, "tasks": ["9.2", "10.1"] },
    { "id": 17, "tasks": ["9.3", "10.2"] },
    { "id": 18, "tasks": ["10.3", "10.4", "10.5", "10.6"] },
    { "id": 19, "tasks": ["10.7", "11.1"] },
    { "id": 20, "tasks": ["11.2", "13.1"] },
    { "id": 21, "tasks": ["13.2", "14.1"] },
    { "id": 22, "tasks": ["14.2"] }
  ]
}
```
