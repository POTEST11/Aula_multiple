/**
 * Mock service implementations.
 * These replace the real API calls when VITE_USE_MOCKS=true.
 * They simulate network delay and return mock data.
 */

import { mockUser, mockClassrooms, mockSubjects, mockActivities } from './data';
import type { Classroom, ClassroomCreate, ClassroomUpdate } from '../types/classroom';
import type { Subject, SubjectCreate } from '../types/subject';
import type { ActivityOutput, GenerateRequest } from '../types/activity';
import type { TokenResponse } from '../types/auth';

// Simulate network latency (200-600ms)
function delay(ms = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms + Math.random() * 300));
}

// Mutable state (persists during session)
let classrooms = [...mockClassrooms];
let subjects = [...mockSubjects];
let activities = [...mockActivities];
let nextClassId = 100;
let nextSubjectId = 100;
let nextActivityId = 100;

// --- Auth mocks ---
export async function mockLogin(): Promise<TokenResponse> {
  await delay();
  const token = 'mock-jwt-token-' + Date.now();
  localStorage.setItem('access_token', token);
  localStorage.setItem('mock_user', JSON.stringify(mockUser));
  return { access_token: token, token_type: 'bearer' };
}

export async function mockRegister(): Promise<TokenResponse> {
  await delay();
  const token = 'mock-jwt-token-' + Date.now();
  localStorage.setItem('access_token', token);
  localStorage.setItem('mock_user', JSON.stringify(mockUser));
  return { access_token: token, token_type: 'bearer' };
}

// --- Classroom mocks ---
export async function mockGetClassrooms(): Promise<Classroom[]> {
  await delay();
  return [...classrooms];
}

export async function mockCreateClassroom(data: ClassroomCreate): Promise<Classroom> {
  await delay();
  const now = new Date().toISOString();
  const newClassroom: Classroom = {
    id: nextClassId++,
    user_id: 1,
    name: data.name,
    grades: data.grades.sort((a, b) => a - b),
    created_at: now,
    updated_at: now,
  };
  classrooms.push(newClassroom);
  return newClassroom;
}

export async function mockUpdateClassroom(id: number, data: ClassroomUpdate): Promise<Classroom> {
  await delay();
  const idx = classrooms.findIndex((c) => c.id === id);
  if (idx === -1) throw new Error('Classroom not found');
  const updated: Classroom = {
    ...classrooms[idx],
    ...(data.name !== undefined && { name: data.name }),
    ...(data.grades !== undefined && { grades: data.grades.sort((a, b) => a - b) }),
    updated_at: new Date().toISOString(),
  };
  classrooms[idx] = updated;
  return updated;
}

export async function mockDeleteClassroom(id: number): Promise<void> {
  await delay();
  classrooms = classrooms.filter((c) => c.id !== id);
  // Preserve activities but clear classroom reference
  activities = activities.map((a) => {
    if (classrooms.find((c) => c.id === id)) {
      return { ...a, classroom_name: null };
    }
    return a;
  });
}

// --- Subject mocks ---
export async function mockGetSubjects(): Promise<Subject[]> {
  await delay();
  return [...subjects];
}

export async function mockCreateSubject(data: SubjectCreate): Promise<Subject> {
  await delay();
  const newSubject: Subject = {
    id: nextSubjectId++,
    user_id: 1,
    name: data.name,
    created_at: new Date().toISOString(),
  };
  subjects.push(newSubject);
  return newSubject;
}

export async function mockDeleteSubject(id: number): Promise<void> {
  await delay();
  subjects = subjects.filter((s) => s.id !== id);
}

// --- Activity / History mocks ---
export async function mockGetHistory(params?: {
  subject_id?: number;
  class_id?: number;
  search?: string;
}): Promise<ActivityOutput[]> {
  await delay();
  let result = [...activities];

  if (params?.class_id) {
    const classroom = classrooms.find((c) => c.id === params.class_id);
    if (classroom) {
      result = result.filter((a) => a.classroom_name === classroom.name);
    }
  }

  if (params?.subject_id) {
    const subject = subjects.find((s) => s.id === params.subject_id);
    if (subject) {
      result = result.filter((a) => a.subject_name === subject.name);
    }
  }

  if (params?.search) {
    const term = params.search.toLowerCase();
    result = result.filter(
      (a) =>
        a.topic.toLowerCase().includes(term) ||
        a.anchor_activity.toLowerCase().includes(term)
    );
  }

  // Sort by date descending
  return result.sort(
    (a, b) => new Date(b.created_at!).getTime() - new Date(a.created_at!).getTime()
  );
}

export async function mockGetActivity(id: number): Promise<ActivityOutput> {
  await delay();
  const activity = activities.find((a) => a.id === id);
  if (!activity) throw new Error('Activity not found');
  return activity;
}

export async function mockDeleteActivity(id: number): Promise<void> {
  await delay();
  activities = activities.filter((a) => a.id !== id);
}

export async function mockGenerateActivity(data: GenerateRequest): Promise<ActivityOutput> {
  // Simulate longer AI processing time (1.5-3s)
  await new Promise((resolve) => setTimeout(resolve, 1500 + Math.random() * 1500));

  const classroom = classrooms.find((c) => c.id === data.classroom_id);
  const newActivity: ActivityOutput = {
    id: nextActivityId++,
    topic: data.topic,
    grades: data.grades,
    subject_name: data.subject_name,
    classroom_name: classroom?.name ?? null,
    available_resources: data.available_resources ?? ['pizarra', 'cuadernos', 'lápices'],
    anchor_activity: `Actividad generada para "${data.topic}": Los estudiantes explorarán este tema a través de actividades prácticas diferenciadas por grado. Se utilizará un enfoque cooperativo donde los estudiantes de grados superiores apoyan a los de grados inferiores, fomentando el aprendizaje entre pares.`,
    variants: data.grades.map((grade) => ({
      grade,
      content: `Contenido adaptado para grado ${grade}: Exploración del tema "${data.topic}" con nivel de complejidad apropiado para estudiantes de ${grade}° grado.`,
      instructions: `Instrucciones para grado ${grade}: 1. Lee el material proporcionado. 2. Realiza la actividad según tu nivel. 3. Comparte con tu grupo lo aprendido. 4. Registra tus conclusiones en el cuaderno.`,
      exercises: `Ejercicios grado ${grade}:\n1. Ejercicio de comprensión básica adaptado al nivel.\n2. Ejercicio de aplicación práctica.\n3. Ejercicio creativo o de extensión.`,
      aligned_standards: [
        {
          country: 'Colombia',
          grade,
          subject: data.subject_name,
          text: `Estándar curricular de ${data.subject_name} para grado ${grade} relacionado con "${data.topic}".`,
          similarity_score: 0.85 + Math.random() * 0.1,
        },
      ],
    })),
    created_at: new Date().toISOString(),
  };

  activities.unshift(newActivity);
  return newActivity;
}
