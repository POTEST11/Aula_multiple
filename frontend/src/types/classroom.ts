export interface Classroom {
  id: number;
  user_id: number;
  name: string;
  grades: number[];
  created_at: string;
  updated_at: string;
}

export interface ClassroomCreate {
  name: string;
  grades: number[];
}

export interface ClassroomUpdate {
  name?: string;
  grades?: number[];
}
