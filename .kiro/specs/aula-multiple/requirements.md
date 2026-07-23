# Requirements Document

## Introduction

Aula Múltiple es un agente especializado que genera actividades pedagógicas diferenciadas por grado para docentes de escuelas unidocentes y multigrado en América Latina. A partir de un tema, los grados presentes en el aula y los recursos disponibles, el sistema produce una actividad "ancla" común con variantes de complejidad adaptadas a cada nivel, alineadas a estándares curriculares oficiales. El sistema mantiene un historial organizado por materia y clase para consulta y reutilización.

## Glossary

- **Agente**: Orquestador basado en LangGraph que coordina los nodos del grafo de generación de actividades pedagógicas.
- **Actividad_Ancla**: Actividad pedagógica central que sirve como base común para todos los grados presentes en el aula.
- **Variante**: Versión de la Actividad_Ancla adaptada en complejidad a un grado escolar específico.
- **Docente**: Usuario principal del sistema; maestro de escuela unidocente o multigrado.
- **Clase**: Grupo de estudiantes de múltiples grados que comparten un mismo espacio y docente.
- **Materia**: Asignatura o área curricular (Matemáticas, Lenguaje, Ciencias, etc.).
- **Estándar_Curricular**: Competencia, logro o indicador de desempeño definido por el currículo oficial de un país latinoamericano.
- **RAG_Curricular**: Módulo de recuperación aumentada por generación que consulta embeddings de estándares curriculares almacenados en pgvector.
- **MCP_Server**: Servidor embebido que expone herramientas de consulta de estándares curriculares al Agente mediante el Model Context Protocol.
- **Historial**: Registro persistente de actividades generadas, organizado por Materia y Clase.
- **API_Backend**: Servicio FastAPI que expone los endpoints REST del sistema.
- **Frontend**: Aplicación React + TypeScript que provee la interfaz web al Docente.
- **Documento_Curricular**: Archivo fuente (PDF) que contiene los Estándares_Curriculares oficiales de un país, publicado por el ministerio de educación correspondiente.
- **Script_Ingesta**: Proceso offline que procesa Documentos_Curriculares y los convierte en embeddings almacenados en pgvector.

## Requirements

### Requisito 1: Generación de Actividad Ancla con Variantes por Grado

**Historia de Usuario:** Como Docente de escuela multigrado, quiero generar una actividad pedagógica común con variantes diferenciadas por grado a partir de un tema, para poder enseñar simultáneamente a estudiantes de distintos niveles sin preparar cada actividad manualmente.

#### Criterios de Aceptación

1. WHEN el Docente envía un tema, una lista de grados (mínimo 2, máximo 6) y una Materia, THE Agente SHALL generar una Actividad_Ancla y una Variante por cada grado especificado.
2. WHEN el Agente genera una Variante, THE Agente SHALL ajustar la complejidad del vocabulario, las instrucciones y los ejercicios al nivel cognitivo correspondiente al grado indicado.
3. WHEN el Agente genera Variantes, THE RAG_Curricular SHALL recuperar los Estándares_Curriculares relevantes para cada grado y Materia consultados.
4. WHEN el RAG_Curricular recupera Estándares_Curriculares, THE Agente SHALL incluir en cada Variante una referencia explícita al Estándar_Curricular alineado.
5. IF el Docente especifica recursos disponibles (pizarra, cuadernos, material reciclable, etc.), THEN THE Agente SHALL adaptar las instrucciones de la actividad para usar exclusivamente esos recursos.
6. IF el Docente no especifica recursos disponibles, THEN THE Agente SHALL generar la actividad asumiendo recursos básicos (pizarra, cuadernos, lápices).

### Requisito 2: Orquestación del Agente mediante Grafo LangGraph

**Historia de Usuario:** Como equipo de desarrollo, quiero que la generación de actividades siga un flujo estructurado de 4 nodos secuenciales, para garantizar calidad y trazabilidad en cada etapa del proceso.

#### Criterios de Aceptación

1. WHEN el Agente recibe una solicitud de generación, THE Agente SHALL ejecutar secuencialmente los nodos: análisis curricular, diseño de actividad, adaptación de recursos y formateo de salida.
2. WHEN el nodo de análisis curricular se ejecuta, THE MCP_Server SHALL exponer la herramienta de consulta de Estándares_Curriculares al Agente.
3. WHEN el nodo de diseño de actividad se ejecuta, THE Agente SHALL producir la estructura de la Actividad_Ancla y las Variantes usando el contexto recuperado por el RAG_Curricular.
4. WHEN el nodo de adaptación de recursos se ejecuta, THE Agente SHALL modificar las instrucciones según los recursos disponibles indicados por el Docente.
5. WHEN el nodo de formateo de salida se ejecuta, THE Agente SHALL producir la actividad en formato estructurado (JSON) con campos separados para la Actividad_Ancla y cada Variante.
6. IF un nodo del grafo falla durante la ejecución, THEN THE Agente SHALL registrar el error con el nombre del nodo fallido y retornar un mensaje descriptivo al Docente.

### Requisito 3: Recuperación de Contexto Curricular (RAG)

**Historia de Usuario:** Como Docente, quiero que las actividades generadas estén alineadas a estándares curriculares oficiales reales, para cumplir con los programas educativos de mi país.

#### Criterios de Aceptación

1. THE RAG_Curricular SHALL almacenar embeddings de Estándares_Curriculares oficiales en PostgreSQL con la extensión pgvector.
2. WHEN el Agente solicita contexto curricular para un grado y Materia, THE RAG_Curricular SHALL recuperar los 5 Estándares_Curriculares con mayor similitud semántica a la consulta.
3. WHEN el RAG_Curricular recupera resultados, THE RAG_Curricular SHALL incluir el país de origen, el grado, la Materia y el texto completo de cada Estándar_Curricular recuperado.
4. IF la consulta al RAG_Curricular no encuentra Estándares_Curriculares con similitud superior al umbral configurado, THEN THE Agente SHALL notificar al Docente que no se encontraron estándares específicos y generar la actividad con lineamientos pedagógicos generales.

### Requisito 4: Gestión de Historial de Actividades

**Historia de Usuario:** Como Docente, quiero consultar y reutilizar actividades que ya generé anteriormente, para no repetir contenido y aprovechar lo que funcionó bien en clase.

#### Criterios de Aceptación

1. WHEN el Agente genera una actividad completa, THE API_Backend SHALL persistir la actividad en el Historial con la fecha, el tema, la Materia, la Clase y los grados asociados.
2. WHEN el Docente solicita el Historial, THE API_Backend SHALL retornar las actividades organizadas por Materia y Clase, ordenadas por fecha descendente.
3. WHEN el Docente busca actividades en el Historial por tema o palabra clave, THE API_Backend SHALL retornar las actividades cuyo tema o contenido coincida con la búsqueda.
4. WHEN el Docente selecciona una actividad del Historial, THE API_Backend SHALL retornar la actividad completa incluyendo la Actividad_Ancla, todas las Variantes y los Estándares_Curriculares asociados.
5. WHEN el Docente elimina una actividad del Historial, THE API_Backend SHALL remover el registro de forma permanente y confirmar la eliminación.

### Requisito 5: Gestión de Materias y Clases

**Historia de Usuario:** Como Docente, quiero registrar mis materias y clases con sus grados, para que el sistema recuerde mi contexto escolar y no tenga que ingresarlo cada vez.

#### Criterios de Aceptación

1. WHEN el Docente crea una Clase, THE API_Backend SHALL almacenar el nombre de la Clase y la lista de grados presentes (mínimo 2, máximo 6).
2. WHEN el Docente crea una Materia, THE API_Backend SHALL almacenar el nombre de la Materia y asociarla al Docente.
3. WHEN el Docente solicita generar una actividad, THE Frontend SHALL permitir seleccionar una Clase y una Materia previamente registradas para autocompletar los grados.
4. WHEN el Docente modifica una Clase, THE API_Backend SHALL actualizar la lista de grados y mantener el Historial existente asociado a dicha Clase.
5. WHEN el Docente elimina una Clase o Materia, THE API_Backend SHALL solicitar confirmación y conservar el Historial previamente generado como registros independientes.

### Requisito 6: Interfaz Web para el Docente

**Historia de Usuario:** Como Docente con conectividad limitada, quiero una interfaz web sencilla y liviana que me permita generar actividades y consultar el historial sin fricciones.

#### Criterios de Aceptación

1. THE Frontend SHALL presentar un formulario de generación con campos para: tema, Clase (con grados), Materia y recursos disponibles (opcional).
2. WHEN el Agente está procesando una solicitud, THE Frontend SHALL mostrar un indicador de progreso con el nodo actual del grafo en ejecución.
3. WHEN el Agente completa la generación, THE Frontend SHALL presentar la Actividad_Ancla y las Variantes de forma separada y legible, permitiendo expandir o colapsar cada grado.
4. THE Frontend SHALL permitir al Docente navegar entre las vistas de generación, historial y gestión de clases/materias desde una barra de navegación principal.
5. THE Frontend SHALL funcionar de forma responsiva en dispositivos móviles y tabletas con un ancho mínimo de 320px.
6. WHILE el Frontend no tiene conexión a internet, THE Frontend SHALL mostrar un mensaje informativo indicando que se requiere conexión para generar actividades.

### Requisito 7: Autenticación Básica del Docente

**Historia de Usuario:** Como Docente, quiero que mi historial y configuración estén protegidos con una cuenta personal, para que otros usuarios no accedan a mis datos.

#### Criterios de Aceptación

1. WHEN el Docente se registra, THE API_Backend SHALL crear una cuenta con correo electrónico y contraseña hasheada.
2. WHEN el Docente inicia sesión con credenciales válidas, THE API_Backend SHALL emitir un token JWT con expiración configurable.
3. IF el Docente envía una solicitud con un token expirado o inválido, THEN THE API_Backend SHALL rechazar la solicitud con código HTTP 401 y un mensaje descriptivo.
4. WHILE el Docente está autenticado, THE API_Backend SHALL restringir el acceso a datos (Historial, Clases, Materias) exclusivamente a los registros del Docente autenticado.

### Requisito 8: API REST del Backend

**Historia de Usuario:** Como equipo de desarrollo, quiero que el backend exponga una API REST clara y documentada, para facilitar la integración con el frontend y posibles clientes futuros.

#### Criterios de Aceptación

1. THE API_Backend SHALL exponer endpoints REST para: generación de actividades, gestión de historial, gestión de clases, gestión de materias y autenticación.
2. WHEN la API_Backend recibe una solicitud con datos inválidos, THE API_Backend SHALL retornar un código HTTP 422 con un mensaje que indique los campos erróneos.
3. WHEN la API_Backend recibe una solicitud de generación, THE API_Backend SHALL validar que la Clase tenga entre 2 y 6 grados antes de invocar al Agente.
4. THE API_Backend SHALL documentar todos los endpoints mediante OpenAPI (Swagger) generado automáticamente por FastAPI.
5. IF el servicio LLM externo (Claude o Groq) no responde en un plazo de 60 segundos, THEN THE API_Backend SHALL cancelar la solicitud y retornar un código HTTP 504 con un mensaje indicando timeout del servicio de IA.

### Requisito 9: Despliegue con Docker

**Historia de Usuario:** Como equipo de desarrollo, quiero que el backend y la base de datos se ejecuten en contenedores Docker, para garantizar reproducibilidad y facilitar el despliegue en cualquier entorno.

#### Criterios de Aceptación

1. THE API_Backend SHALL ejecutarse dentro de un contenedor Docker con todas las dependencias Python instaladas.
2. THE PostgreSQL con pgvector SHALL ejecutarse dentro de un contenedor Docker con volumen persistente para los datos.
3. WHEN se ejecuta `docker compose up`, THE sistema SHALL levantar el backend, la base de datos y aplicar las migraciones de esquema automáticamente.
4. THE sistema SHALL utilizar variables de entorno para configurar credenciales de base de datos, claves de API del LLM y parámetros del servidor.
5. IF un contenedor falla durante la inicialización, THEN THE sistema SHALL registrar el error en la salida estándar del contenedor con contexto suficiente para diagnóstico.

### Requisito 10: Ingesta de Estándares Curriculares

**Historia de Usuario:** Como equipo de desarrollo, quiero un proceso reproducible que convierta los documentos curriculares oficiales en embeddings consultables, para que el RAG_Curricular tenga datos reales sobre los cuales recuperar contexto.

#### Criterios de Aceptación

1. THE sistema SHALL proveer un Script_Ingesta que procese Documentos_Curriculares en formato PDF y extraiga su contenido textual.
2. WHEN el Script_Ingesta procesa un Documento_Curricular, THE Script_Ingesta SHALL dividir el texto en fragmentos (chunks) y generar un embedding vectorial por cada fragmento.
3. WHEN el Script_Ingesta genera un embedding, THE Script_Ingesta SHALL almacenarlo en pgvector junto con metadatos de país, grado, Materia y el texto original del fragmento.
4. THE Script_Ingesta SHALL ejecutarse de forma independiente al API_Backend, sin requerir que el servidor esté corriendo.
5. IF el Script_Ingesta procesa un Documento_Curricular que ya fue ingresado previamente, THEN THE Script_Ingesta SHALL evitar duplicar los embeddings correspondientes.