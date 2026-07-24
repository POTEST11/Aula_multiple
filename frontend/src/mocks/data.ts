/**
 * Mock data for frontend development without backend.
 * Simulates all API responses with realistic educational content.
 */

import type { User } from '../types/auth';
import type { Classroom } from '../types/classroom';
import type { Subject } from '../types/subject';
import type { ActivityOutput } from '../types/activity';

// --- User ---
export const mockUser: User = {
  id: 1,
  email: 'maria.gonzalez@escuela.edu.co',
  name: 'María González',
  created_at: '2025-01-15T10:30:00Z',
};

// --- Subjects ---
export const mockSubjects: Subject[] = [
  { id: 1, user_id: 1, name: 'Matemáticas', created_at: '2025-01-20T08:00:00Z' },
  { id: 2, user_id: 1, name: 'Lenguaje', created_at: '2025-01-20T08:05:00Z' },
  { id: 3, user_id: 1, name: 'Ciencias Naturales', created_at: '2025-02-01T09:00:00Z' },
  { id: 4, user_id: 1, name: 'Ciencias Sociales', created_at: '2025-02-10T11:00:00Z' },
  { id: 5, user_id: 1, name: 'Educación Artística', created_at: '2025-03-05T14:00:00Z' },
];

// --- Classrooms ---
export const mockClassrooms: Classroom[] = [
  {
    id: 1,
    user_id: 1,
    name: 'Multigrado A - Mañana',
    grades: [2, 3, 4],
    created_at: '2025-01-22T09:00:00Z',
    updated_at: '2025-07-10T14:30:00Z',
  },
  {
    id: 2,
    user_id: 1,
    name: 'Multigrado B - Tarde',
    grades: [4, 5, 6],
    created_at: '2025-01-22T09:30:00Z',
    updated_at: '2025-07-18T11:00:00Z',
  },
  {
    id: 3,
    user_id: 1,
    name: 'Refuerzo Matemáticas',
    grades: [3, 4],
    created_at: '2025-03-10T10:00:00Z',
    updated_at: '2025-06-25T09:15:00Z',
  },
  {
    id: 4,
    user_id: 1,
    name: 'Ciencias Integradas',
    grades: [2, 3, 4, 5],
    created_at: '2025-04-01T08:00:00Z',
    updated_at: '2025-07-20T16:45:00Z',
  },
  {
    id: 5,
    user_id: 1,
    name: 'Lectura y Escritura Creativa',
    grades: [3, 4, 5, 6],
    created_at: '2025-05-15T12:00:00Z',
    updated_at: '2025-07-22T10:20:00Z',
  },
];

// --- Activities (History) ---
export const mockActivities: ActivityOutput[] = [
  {
    id: 1,
    topic: 'Fracciones con material concreto',
    grades: [2, 3, 4],
    subject_name: 'Matemáticas',
    classroom_name: 'Multigrado A - Mañana',
    available_resources: ['pizarra', 'cuadernos', 'papel de colores', 'tijeras'],
    anchor_activity:
      'Los estudiantes explorarán el concepto de fracciones dividiendo figuras geométricas (círculos y rectángulos) en partes iguales usando papel de colores. Cada grupo trabajará con las mismas figuras pero con niveles de complejidad diferenciados según su grado. Al final, presentarán sus creaciones al resto de la clase explicando qué fracción representaron.',
    variants: [
      {
        grade: 2,
        content:
          'Introducción al concepto de "mitad" y "cuarto" mediante la manipulación directa de figuras recortadas.',
        instructions:
          'Dobla un círculo de papel por la mitad. Colorea una mitad. Repite con un rectángulo. Ahora dobla otro círculo en 4 partes iguales y colorea una parte. Dibuja en tu cuaderno lo que hiciste.',
        exercises:
          '1. Colorea la mitad de cada figura.\n2. Divide el rectángulo en 4 partes iguales.\n3. ¿Cuántas mitades tiene un círculo entero?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 2,
            subject: 'Matemáticas',
            text: 'Reconoce y representa fracciones unitarias (1/2, 1/4) en contextos concretos.',
            similarity_score: 0.92,
          },
        ],
      },
      {
        grade: 3,
        content:
          'Representación de fracciones simples (1/2, 1/3, 1/4, 1/6) y comparación visual de tamaños.',
        instructions:
          'Recorta círculos de papel y divídelos en 2, 3, 4 y 6 partes iguales. Etiqueta cada parte con su fracción. Ordena las fracciones de mayor a menor pegándolas en tu cuaderno. Escribe una oración comparando dos fracciones.',
        exercises:
          '1. Divide un círculo en tercios y colorea 2/3.\n2. ¿Qué es más grande: 1/3 o 1/4? Demuéstralo con tus recortes.\n3. Escribe tres fracciones que sean menores que 1/2.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 3,
            subject: 'Matemáticas',
            text: 'Compara fracciones simples utilizando representaciones gráficas y material concreto.',
            similarity_score: 0.89,
          },
        ],
      },
      {
        grade: 4,
        content:
          'Suma de fracciones con igual denominador y representación en la recta numérica.',
        instructions:
          'Usa tiras de papel divididas en partes iguales para representar sumas de fracciones con el mismo denominador. Luego ubica las fracciones resultantes en una recta numérica dibujada en tu cuaderno. Inventa un problema de la vida real que se resuelva con suma de fracciones.',
        exercises:
          '1. Calcula y representa: 1/4 + 2/4 = ?\n2. Ubica en la recta numérica: 0, 1/6, 2/6, 3/6, 4/6, 5/6, 1.\n3. Inventa un problema donde sumes fracciones con denominador 8.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 4,
            subject: 'Matemáticas',
            text: 'Resuelve problemas que involucran la suma de fracciones homogéneas y las representa en la recta numérica.',
            similarity_score: 0.91,
          },
        ],
      },
    ],
    created_at: '2025-07-10T14:30:00Z',
  },
  {
    id: 2,
    topic: 'El ciclo del agua',
    grades: [4, 5, 6],
    subject_name: 'Ciencias Naturales',
    classroom_name: 'Multigrado B - Tarde',
    available_resources: ['pizarra', 'cuadernos', 'botella plástica', 'hielo', 'agua caliente'],
    anchor_activity:
      'Los estudiantes observarán un experimento demostrativo del ciclo del agua usando una botella plástica con agua caliente y hielo. A partir de la observación, cada grupo documentará las etapas del ciclo del agua con diferente nivel de profundidad según su grado.',
    variants: [
      {
        grade: 4,
        content:
          'Identificación de las 3 etapas principales del ciclo del agua: evaporación, condensación y precipitación.',
        instructions:
          'Observa el experimento. Dibuja lo que ves en 3 pasos. Etiqueta cada dibujo con el nombre de la etapa. Escribe una oración describiendo qué pasa en cada etapa.',
        exercises:
          '1. Nombra las 3 etapas del ciclo del agua.\n2. ¿Qué etapa viste cuando el vapor tocó el hielo?\n3. Dibuja el ciclo del agua con flechas.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 4,
            subject: 'Ciencias Naturales',
            text: 'Describe el ciclo del agua identificando los cambios de estado involucrados.',
            similarity_score: 0.94,
          },
        ],
      },
      {
        grade: 5,
        content:
          'Relación entre el ciclo del agua y los factores climáticos (temperatura, presión, altitud).',
        instructions:
          'Observa el experimento y registra tus observaciones en una tabla. Investiga cómo la temperatura afecta la velocidad de evaporación. Elabora un diagrama del ciclo del agua que incluya la infiltración y la escorrentía. Escribe un párrafo explicando por qué llueve más en unas regiones que en otras.',
        exercises:
          '1. ¿Qué pasaría si calentamos más el agua? ¿Y si usamos menos hielo?\n2. Explica la diferencia entre escorrentía e infiltración.\n3. ¿Por qué las montañas altas suelen tener más precipitación?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 5,
            subject: 'Ciencias Naturales',
            text: 'Explica la relación entre los factores climáticos y el ciclo hidrológico en diferentes ecosistemas.',
            similarity_score: 0.87,
          },
        ],
      },
      {
        grade: 6,
        content:
          'Impacto humano en el ciclo del agua: contaminación, deforestación y cambio climático.',
        instructions:
          'Observa el experimento y formula una hipótesis sobre qué pasaría si hubiera contaminantes en el agua. Investiga cómo la deforestación altera el ciclo del agua en tu región. Redacta un ensayo corto (1 página) sobre el impacto del cambio climático en los recursos hídricos de América Latina, proponiendo al menos 2 soluciones.',
        exercises:
          '1. ¿Cómo afecta la tala de árboles a la infiltración del agua?\n2. Diseña un experimento para medir evaporación en superficies con y sin vegetación.\n3. Propón 3 acciones concretas para proteger las fuentes de agua en tu comunidad.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 6,
            subject: 'Ciencias Naturales',
            text: 'Analiza el impacto de las actividades humanas en los ciclos biogeoquímicos y propone acciones de conservación.',
            similarity_score: 0.85,
          },
        ],
      },
    ],
    created_at: '2025-07-18T11:00:00Z',
  },
  {
    id: 3,
    topic: 'Escritura de cuentos cortos con estructura narrativa',
    grades: [3, 4, 5, 6],
    subject_name: 'Lenguaje',
    classroom_name: 'Lectura y Escritura Creativa',
    available_resources: ['cuadernos', 'lápices de colores', 'hojas blancas'],
    anchor_activity:
      'Todos los estudiantes escribirán un cuento corto basado en un tema común: "Un animal que descubre algo nuevo". La complejidad de la estructura narrativa y los requisitos de extensión varían por grado. Al finalizar, cada estudiante leerá su cuento al grupo y recibirá retroalimentación de sus compañeros.',
    variants: [
      {
        grade: 3,
        content: 'Cuento de 5-8 oraciones con inicio, desarrollo y final claro.',
        instructions:
          'Piensa en un animal. ¿Qué descubre? Dibuja 3 escenas: inicio, desarrollo y final. Escribe debajo de cada dibujo 2-3 oraciones contando qué pasa. Usa mayúsculas al inicio y punto al final de cada oración.',
        exercises:
          '1. Escribe tu cuento en 3 partes con dibujos.\n2. Subraya los nombres propios con rojo.\n3. Lee tu cuento a un compañero y pregúntale qué parte le gustó más.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 3,
            subject: 'Lenguaje',
            text: 'Produce textos narrativos breves con estructura de inicio, nudo y desenlace.',
            similarity_score: 0.90,
          },
        ],
      },
      {
        grade: 4,
        content: 'Cuento de 10-15 oraciones con descripción del personaje y diálogos simples.',
        instructions:
          'Escribe un cuento sobre un animal que descubre algo nuevo. Incluye: una descripción física del animal (al menos 3 características), un diálogo entre dos personajes, y un problema que el animal debe resolver. Usa conectores: "primero", "luego", "entonces", "finalmente".',
        exercises:
          '1. Escribe tu cuento usando al menos 4 conectores temporales.\n2. Incluye un diálogo de al menos 3 turnos entre personajes.\n3. Revisa tu texto: ¿tiene inicio, problema y solución?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 4,
            subject: 'Lenguaje',
            text: 'Escribe textos narrativos con elementos descriptivos y dialogales, usando conectores temporales.',
            similarity_score: 0.88,
          },
        ],
      },
      {
        grade: 5,
        content: 'Cuento de 1 página con narrador definido, conflicto desarrollado y resolución.',
        instructions:
          'Escribe un cuento de al menos una página. Elige un tipo de narrador (primera o tercera persona). Desarrolla un conflicto claro que el personaje principal deba enfrentar. Incluye al menos una descripción del ambiente. Usa al menos 2 signos de puntuación diferentes además del punto (comas, signos de exclamación, interrogación).',
        exercises:
          '1. Escribe tu cuento indicando qué tipo de narrador elegiste y por qué.\n2. Subraya con verde las descripciones del ambiente.\n3. Intercambia tu cuento con un compañero y escribe 2 sugerencias de mejora.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 5,
            subject: 'Lenguaje',
            text: 'Produce textos narrativos con estructura completa, punto de vista definido y uso adecuado de signos de puntuación.',
            similarity_score: 0.86,
          },
        ],
      },
      {
        grade: 6,
        content: 'Cuento de 1.5-2 páginas con técnicas narrativas avanzadas y moraleja implícita.',
        instructions:
          'Escribe un cuento de al menos 1.5 páginas. Usa al menos una técnica narrativa avanzada: flashback, suspenso, o cambio de perspectiva. El cuento debe tener una moraleja o enseñanza implícita (no explícita). Incluye al menos 2 figuras retóricas (metáfora, símil, personificación). Revisa tu texto asegurándote de la coherencia y cohesión entre párrafos.',
        exercises:
          '1. Escribe tu cuento usando al menos una técnica narrativa avanzada.\n2. Identifica y subraya las figuras retóricas que usaste.\n3. Escribe un párrafo de autoevaluación: ¿qué hiciste bien y qué mejorarías?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 6,
            subject: 'Lenguaje',
            text: 'Produce textos narrativos literarios empleando técnicas y recursos estilísticos con coherencia y cohesión textual.',
            similarity_score: 0.84,
          },
        ],
      },
    ],
    created_at: '2025-07-22T10:20:00Z',
  },
  {
    id: 4,
    topic: 'Resolución de problemas con multiplicación',
    grades: [3, 4],
    subject_name: 'Matemáticas',
    classroom_name: 'Refuerzo Matemáticas',
    available_resources: ['pizarra', 'cuadernos', 'lápices'],
    anchor_activity:
      'Los estudiantes resolverán problemas de multiplicación contextualizados en situaciones de la vida cotidiana rural (cosechas, animales, distribución de alimentos). Cada grado trabaja con números y situaciones de complejidad diferenciada.',
    variants: [
      {
        grade: 3,
        content: 'Multiplicación como suma repetida con números de una cifra.',
        instructions:
          'Lee cada problema. Dibuja grupos iguales para representar la situación. Escribe la suma repetida y luego la multiplicación correspondiente. Comprueba tu resultado contando los objetos dibujados.',
        exercises:
          '1. Don Pedro tiene 4 gallinas. Cada gallina pone 3 huevos por semana. ¿Cuántos huevos hay en total?\n2. En la huerta hay 5 filas de lechugas con 6 lechugas cada fila. ¿Cuántas lechugas hay?\n3. Inventa un problema que se resuelva con 7 × 4.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 3,
            subject: 'Matemáticas',
            text: 'Resuelve problemas de estructura multiplicativa usando la suma repetida y arreglos rectangulares.',
            similarity_score: 0.93,
          },
        ],
      },
      {
        grade: 4,
        content: 'Multiplicación de números de dos cifras y problemas de varios pasos.',
        instructions:
          'Lee cada problema e identifica los datos y la pregunta. Decide qué operaciones necesitas (puede haber más de una). Resuelve paso a paso mostrando tu procedimiento completo. Verifica tu respuesta con una estimación.',
        exercises:
          '1. La cooperativa recogió 24 canastas de naranjas con 35 naranjas cada una. ¿Cuántas naranjas recogieron en total?\n2. Si se reparten las naranjas entre 12 familias, ¿cuántas le tocan a cada una? ¿Sobran?\n3. El mercado vende cada naranja a $200. ¿Cuánto dinero se obtiene por las 5 canastas más pequeñas (28 naranjas cada una)?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 4,
            subject: 'Matemáticas',
            text: 'Resuelve problemas multiplicativos de varios pasos involucrando números hasta de cuatro cifras.',
            similarity_score: 0.90,
          },
        ],
      },
    ],
    created_at: '2025-06-25T09:15:00Z',
  },
  {
    id: 5,
    topic: 'Los ecosistemas de nuestra región',
    grades: [2, 3, 4, 5],
    subject_name: 'Ciencias Naturales',
    classroom_name: 'Ciencias Integradas',
    available_resources: ['pizarra', 'cuadernos', 'láminas impresas', 'material reciclable'],
    anchor_activity:
      'Los estudiantes explorarán los ecosistemas presentes en su región (bosque, río, zona agrícola) a través de la observación de láminas y la construcción de maquetas grupales con material reciclable. Cada grado analiza los ecosistemas con diferente profundidad.',
    variants: [
      {
        grade: 2,
        content: 'Identificación de seres vivos y no vivos en un ecosistema cercano.',
        instructions:
          'Observa la lámina del ecosistema del río. Señala con el dedo los seres vivos (animales, plantas) y las cosas no vivas (agua, rocas, tierra). Dibuja el ecosistema separando vivos y no vivos con un color diferente.',
        exercises:
          '1. Dibuja 3 seres vivos y 3 no vivos del río.\n2. ¿El agua es un ser vivo? ¿Por qué?\n3. ¿Qué pasaría si no hubiera agua en el río?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 2,
            subject: 'Ciencias Naturales',
            text: 'Clasifica seres vivos y no vivos a partir de la observación de su entorno inmediato.',
            similarity_score: 0.91,
          },
        ],
      },
      {
        grade: 3,
        content: 'Relaciones básicas entre seres vivos: alimentación y hábitat.',
        instructions:
          'Observa la lámina y forma cadenas alimenticias sencillas (quién come a quién). Dibuja una cadena alimenticia de 3 eslabones del ecosistema del bosque. Explica dónde vive cada animal y por qué.',
        exercises:
          '1. Dibuja una cadena alimenticia: planta → herbívoro → carnívoro.\n2. ¿Por qué el sapo vive cerca del río?\n3. ¿Qué pasaría si desaparecen las plantas?',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 3,
            subject: 'Ciencias Naturales',
            text: 'Identifica relaciones alimenticias entre organismos de un ecosistema local.',
            similarity_score: 0.88,
          },
        ],
      },
      {
        grade: 4,
        content: 'Componentes de un ecosistema y flujo de energía.',
        instructions:
          'Identifica los factores bióticos y abióticos del ecosistema asignado. Construye con tu grupo una maqueta usando material reciclable. Elabora un diagrama de flujo de energía desde el sol hasta los descomponedores. Presenta tu maqueta explicando las relaciones.',
        exercises:
          '1. Lista 5 factores bióticos y 5 abióticos de tu ecosistema.\n2. Dibuja una red alimenticia (no cadena) con al menos 6 organismos.\n3. Explica qué hacen los descomponedores.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 4,
            subject: 'Ciencias Naturales',
            text: 'Explica el flujo de energía en los ecosistemas identificando productores, consumidores y descomponedores.',
            similarity_score: 0.90,
          },
        ],
      },
      {
        grade: 5,
        content: 'Impacto humano en los ecosistemas y propuestas de conservación.',
        instructions:
          'Investiga cómo las actividades humanas (agricultura, ganadería, urbanización) han afectado un ecosistema de tu región. Compara el ecosistema antes y después de la intervención humana. Propone un plan de conservación con 3 acciones concretas y presenta un afiche informativo.',
        exercises:
          '1. Compara con un diagrama de Venn: ecosistema natural vs. ecosistema intervenido.\n2. ¿Qué especies se han perdido o están en peligro en tu región?\n3. Diseña un afiche con 3 acciones de conservación para tu comunidad.',
        aligned_standards: [
          {
            country: 'Colombia',
            grade: 5,
            subject: 'Ciencias Naturales',
            text: 'Analiza los efectos de las actividades humanas sobre los ecosistemas y propone estrategias de conservación.',
            similarity_score: 0.86,
          },
        ],
      },
    ],
    created_at: '2025-07-20T16:45:00Z',
  },
];
