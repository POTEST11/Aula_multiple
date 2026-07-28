# Aula Múltiple

**Asistente de IA para docentes de escuelas multigrado en zonas rurales de Colombia**

Genera actividades pedagógicas diferenciadas por grado, alineadas a los estándares curriculares oficiales del MEN, para que un solo docente pueda enseñar simultáneamente a estudiantes de distintos niveles sin preparar cada actividad de forma manual.

---

## La Problemática

En Colombia, el 67% de las 55.889 sedes educativas se localiza en zonas rurales. La mayoría opera bajo el modelo multigrado: un solo docente atiende estudiantes de 2 a 6 grados diferentes en la misma aula y al mismo tiempo. Esta realidad, documentada por el DANE y el Laboratorio de Economía de la Educación de la U. Javeriana, implica condiciones estructurales críticas:

- **79,8%** de las sedes rurales no cuenta con acceso a internet.
- **59,7%** carece de aulas de informática.
- **18,1%** no tiene servicio de energía eléctrica.
- Menos de la mitad de los estudiantes que ingresan a primero de primaria en zonas rurales completa sus estudios.

El docente multigrado enfrenta un desafío único: debe planificar contenidos, actividades y evaluaciones diferenciadas para cada grado, todo dentro de una misma sesión de clase. Esto multiplica su carga de planeación por el número de grados que atiende, consumiendo tiempo que podría dedicar a la interacción pedagógica directa.

No existen herramientas digitales diseñadas específicamente para este contexto. Las plataformas educativas existentes asumen aulas monogrado con conectividad estable — una realidad que no corresponde al campo colombiano.

**Fuentes:**

- [DANE — Estadísticas de educación](https://www.dane.gov.co/index.php/estadisticas-por-tema/educacion)
- [Laboratorio de Economía de la Educación, U. Javeriana — Informe sobre educación rural](https://lee.javeriana.edu.co/w/lee-informe-98)
- [La República — Características de la educación en zonas rurales (2023)](https://www.larepublica.co/economia/caracteristicas-de-la-educacion-en-zonas-rurales-3719292)
- [El Espectador — Cifras del panorama de la educación rural](https://www.elespectador.com/educacion/las-cifras-que-muestran-el-complejo-panorama-de-la-educacion-rural-en-colombia/)

---

## La Solución

Aula Múltiple es un agente de inteligencia artificial que automatiza la generación de actividades pedagógicas para aulas multigrado. El docente ingresa un tema, selecciona su clase (con los grados presentes) y la materia. El sistema produce:

1. **Una actividad ancla** — actividad común con un hilo conductor que permite la participación colaborativa entre todos los grados.
2. **Variantes diferenciadas por grado** — cada variante ajusta vocabulario, instrucciones y ejercicios al nivel cognitivo correspondiente.
3. **Alineación curricular verificable** — cada variante referencia explícitamente los Derechos Básicos de Aprendizaje (DBA) del MEN de Colombia correspondientes al grado y materia.

El sistema también valida que el tema solicitado corresponda a la malla curricular oficial. Si un docente solicita un tema fuera del currículo para un grado específico, el agente lo notifica y genera la actividad basándose en los estándares que sí corresponden.

### Impacto esperado

- Reducción del tiempo de planeación diferenciada de horas a minutos.
- Garantía de alineación curricular con los DBA oficiales del MEN.
- Actividades ejecutables directamente, adaptadas a los recursos reales del docente (pizarra, cuadernos, material reciclable).
- Historial reutilizable organizado por clase y materia.

---

## Demo

<!-- VIDEO DEMO PLACEHOLDER -->
[![demo](https://img.youtube.com/vi/dsCg-1HTFEA/0.jpg)](https://www.youtube.com/watch?v=dsCg-1HTFEA)


**Deploy:** [http://54.83.132.113](http://54.83.132.113)

---

## Arquitectura

### Infraestructura AWS (Producción)

```mermaid
graph TB
    subgraph AWS["AWS — us-east-1"]
        subgraph EC2["EC2 t3.small — Amazon Linux 2023 + Docker"]
            subgraph DockerNet["Docker Compose Network"]
                FE["nginx:alpine<br/>Frontend SPA<br/>Puerto :80"]
                BE["python:3.11-slim<br/>Backend FastAPI + LangGraph<br/>Puerto :8000"]
            end
        end

        RDS["Amazon RDS<br/>PostgreSQL 16 + pgvector<br/>db.t3.micro · 20GB"]
        S3["Amazon S3<br/>aula-multiple-uploads<br/>PDFs e imágenes"]
    end

    LLM["OpenRouter API<br/>meta-llama/llama-3.3-70b-instruct"]
    USER(("Docente"))

    USER -->|HTTP :80| FE
    FE -->|proxy /api| BE
    BE -->|asyncpg| RDS
    BE -.->|uploads| S3
    BE -->|HTTPS| LLM
```

### Arquitectura de la Aplicación

```mermaid
graph TB
    subgraph Frontend["Frontend — React 19 + TypeScript + Vite"]
        UI["Interfaz Docente"]
        PAGES["Home · Login · Dashboard<br/>Classes · ClassDetail (chat)<br/>History · Subjects"]
    end

    subgraph Backend["Backend — FastAPI · Monolito Modular"]
        API["API REST /api/v1"]
        AUTH["Auth JWT + bcrypt"]
        CRUD["CRUD<br/>Clases · Materias · Historial"]
        DOCS["Document Processor<br/>PDF/OCR → Chunks → Embeddings"]

        subgraph Agent["Agente LangGraph — 4 Nodos Secuenciales"]
            N1["① Análisis Curricular<br/>RAG dual: pgvector search"]
            N2["② Diseño de Actividad<br/>LLM genera ancla + variantes"]
            N3["③ Adaptación de Recursos<br/>LLM adapta a pizarra/cuadernos"]
            N4["④ Formateo de Salida<br/>Pydantic validation"]
            N1 --> N2 --> N3 --> N4
        end

        subgraph RAG["RAG Dual"]
            GLOBAL["Retriever Curricular<br/>DBA oficiales MEN · 5 materias"]
            CLASS["Retriever por Clase<br/>Documentos propios del docente"]
        end

        subgraph Emb["Embeddings Locales · CPU"]
            ST["sentence-transformers<br/>all-MiniLM-L6-v2 · 384 dimensiones"]
        end

        MCP["MCP Server Embebido<br/>FastMCP in-process"]
    end

    subgraph DB["Amazon RDS — PostgreSQL 16 + pgvector"]
        REL["Tablas relacionales<br/>users · classrooms · subjects<br/>activities · variants · standards"]
        VEC["Tablas vectoriales<br/>curriculum_embeddings (233 chunks)<br/>document_embeddings"]
    end

    LLM2["OpenRouter<br/>Llama 3.3 70B Instruct"]

    UI -->|HTTP/JSON| API
    API --> AUTH
    API --> CRUD
    API --> DOCS
    API --> Agent
    N1 -->|tool_call| MCP
    MCP --> RAG
    RAG --> Emb
    Emb --> VEC
    GLOBAL --> VEC
    CLASS --> VEC
    N2 --> LLM2
    N3 --> LLM2
    CRUD --> REL
    DOCS --> VEC
```

### Pipeline de Generación de Actividades

```mermaid
sequenceDiagram
    participant D as Docente
    participant F as Frontend (nginx)
    participant A as FastAPI
    participant G as LangGraph
    participant E as Embeddings (CPU)
    participant DB as RDS pgvector
    participant L as OpenRouter (Llama 3.3 70B)

    D->>F: Escribe tema en chat de clase
    F->>A: POST /api/v1/activities/generate
    A->>A: Valida JWT + grados (2-6)

    rect rgb(240, 248, 255)
        Note over G: ① Análisis Curricular
        A->>G: Invoca grafo
        G->>E: Embedding del tema (384d, local CPU)
        G->>DB: Cosine similarity → DBA + docs clase
        DB-->>G: Estándares curriculares + contexto
    end

    rect rgb(255, 248, 240)
        Note over G: ② Diseño de Actividad
        G->>L: Prompt + tema + estándares + grados
        L-->>G: Actividad ancla + variantes por grado
    end

    rect rgb(240, 255, 240)
        Note over G: ③ Adaptación de Recursos
        G->>L: Prompt + actividad + recursos disponibles
        L-->>G: Actividad adaptada a contexto real
    end

    rect rgb(248, 240, 255)
        Note over G: ④ Formateo de Salida
        G->>G: Validación Pydantic → ActivityOutput
    end

    G-->>A: Actividad completa (JSON)
    A->>DB: INSERT historial
    A-->>F: Response
    F-->>D: Actividad ancla + variantes colapsables
```

### Pipeline de Procesamiento de Documentos

```mermaid
flowchart LR
    UPLOAD["📄 Docente sube<br/>PDF o Imagen<br/>(max 20MB)"]
    SAVE["💾 Guardar en disco<br/>status = pending"]
    EXTRACT["📝 Extracción<br/>PDF: pdfplumber<br/>IMG: Tesseract OCR"]
    CHUNK["✂️ Chunking<br/>500 chars · 50 overlap"]
    EMBED["🧠 Embeddings<br/>all-MiniLM-L6-v2<br/>384 dimensiones"]
    STORE["🗄️ pgvector<br/>SHA-256 dedup<br/>status = ready"]

    UPLOAD --> SAVE --> EXTRACT --> CHUNK --> EMBED --> STORE
```

---

## Innovación Técnica

| Componente | Decisión | Ventaja competitiva |
| --- | --- | --- |
| **Agente LangGraph con 4 nodos** | Pipeline secuencial orquestado como grafo de estados | Cada nodo tiene responsabilidad única; el flujo es trazable y depurable |
| **RAG Dual (global + por clase)** | Dos retrievers independientes consultan pgvector | Combina currículo oficial con material propio del docente |
| **Embeddings locales** | sentence-transformers (all-MiniLM-L6-v2, 384d) corriendo en CPU | Sin costo, sin dependencia de API externa, funciona offline para la búsqueda semántica |
| **MCP Server embebido** | Model Context Protocol in-process vía FastMCP | El agente accede a herramientas de consulta curricular como tool calls nativos |
| **Validación curricular en prompt** | El prompt compara tema vs. DBA oficiales | Previene generación de contenido fuera de la malla curricular |
| **Procesamiento de documentos** | Pipeline asíncrono: PDF/OCR → chunking → embedding → pgvector | El docente sube materiales propios que enriquecen la generación |
| **Base de datos unificada** | PostgreSQL con pgvector para datos relacionales + vectoriales | Un solo motor simplifica operaciones y deployment |
| **Property-based testing** | 20+ propiedades formales verificadas con Hypothesis | Garantías de corrección sobre invariantes del sistema |

### Frente a alternativas existentes

Las plataformas educativas con IA actuales (ChatGPT, Gemini, herramientas de lesson planning) no resuelven el problema multigrado porque:

- Generan actividades para un solo grado a la vez.
- No conocen ni validan contra currículos oficiales latinoamericanos.
- No producen una actividad ancla compartida con variantes diferenciadas.
- No permiten subir documentos propios como contexto RAG por clase.
- No están diseñadas para operar con recursos mínimos (pizarra y cuadernos).

---

## Stack Tecnológico

**Backend:**

- Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · Alembic
- LangGraph · LangChain Core · MCP (Model Context Protocol)
- sentence-transformers · pgvector · pdfplumber · pytesseract
- Hypothesis (property-based testing) · pytest

**Frontend:**

- React 19 · TypeScript 6 · Vite 8 · React Router 7
- CSS Modules · Diseño responsivo (min 320px)

**Infraestructura:**

- Docker Compose (nginx + backend + PostgreSQL pgvector)
- Amazon EC2 t3.small · Amazon RDS db.t3.micro · Amazon S3

**LLM:**

- OpenRouter → meta-llama/llama-3.3-70b-instruct

**Datos curriculares:**

- Derechos Básicos de Aprendizaje (DBA) V2 — MEN Colombia
- 5 materias · Grados 1-6 · 233 chunks embedidos

---

## Servicios AWS

| Servicio | Uso en producción |
| --- | --- |
| **Amazon EC2** (t3.small) | Hosting de la aplicación completa via Docker Compose |
| **Amazon RDS** (PostgreSQL 16 + pgvector) | Base de datos relacional y vectorial |
| **Amazon S3** | Almacenamiento de documentos subidos por docentes |

---

## Estructura del Proyecto

```text
aula_multiple/
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph: grafo, 4 nodos, prompts, estado
│   │   ├── api/            # Endpoints REST (auth, clases, materias, historial, documentos)
│   │   ├── auth/           # JWT + bcrypt
│   │   ├── crud/           # Operaciones de base de datos
│   │   ├── mcp_server/     # MCP Server embebido (FastMCP)
│   │   ├── models/         # SQLAlchemy models (8 tablas)
│   │   ├── rag/            # Retrievers + servicio de embeddings local
│   │   ├── schemas/        # Pydantic request/response
│   │   └── services/       # Document processor (PDF, OCR, chunking)
│   ├── curriculum_data/    # DBA oficiales en markdown (5 materias)
│   ├── scripts/            # Ingesta de currículo
│   ├── tests/              # 26 archivos de test (property-based + integration)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # Layout, Navbar, Sidebar, ProtectedRoute
│   │   ├── pages/          # Home, Login, Register, Dashboard/*
│   │   ├── services/       # API clients (axios)
│   │   ├── hooks/          # useAuth
│   │   └── types/          # TypeScript interfaces
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Modelo de Datos

```mermaid
erDiagram
    USER ||--o{ CLASSROOM : owns
    USER ||--o{ SUBJECT : owns
    USER ||--o{ ACTIVITY : generates
    CLASSROOM ||--o{ ACTIVITY : associated
    CLASSROOM ||--o{ CLASS_DOCUMENT : has
    CLASS_DOCUMENT ||--o{ DOCUMENT_EMBEDDING : contains
    ACTIVITY ||--o{ ACTIVITY_VARIANT : contains
    ACTIVITY_VARIANT ||--o{ VARIANT_STANDARD : references

    CURRICULUM_EMBEDDING {
        vector embedding_384d
        string country
        int grade
        string subject
        text content
    }

    DOCUMENT_EMBEDDING {
        vector embedding_384d
        int classroom_id
        text content
        string content_hash
    }
```

---

## Licencia

MIT
