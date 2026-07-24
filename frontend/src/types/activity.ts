export interface CurriculumStandard {
  country: string;
  grade: number;
  subject: string;
  text: string;
  similarity_score: number | null;
}

export interface VariantOutput {
  grade: number;
  content: string;
  instructions: string;
  exercises: string;
  aligned_standards: CurriculumStandard[];
}

export interface ActivityOutput {
  id: number | null;
  topic: string;
  grades: number[];
  subject_name: string;
  classroom_name: string | null;
  available_resources: string[];
  anchor_activity: string;
  variants: VariantOutput[];
  created_at: string | null;
}

export interface GenerateRequest {
  topic: string;
  classroom_id: number | null;
  subject_id: number | null;
  grades: number[];
  subject_name: string;
  available_resources: string[] | null;
}
