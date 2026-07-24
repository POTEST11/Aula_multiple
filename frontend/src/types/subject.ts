export interface Subject {
  id: number;
  user_id: number;
  name: string;
  created_at: string;
}

export interface SubjectCreate {
  name: string;
}
