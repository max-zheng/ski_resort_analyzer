export interface Categories {
  [key: string]: number | null;
}

export interface Rating {
  confidence: number;
  notes: string;
  categories: Categories;
}

export interface Camera {
  camera_name: string;
  image_url: string | null;
  is_base64: boolean;
  rating: Rating | null;
  error: string | null;
}

export interface Resort {
  resort_name: string;
  resort_key: string;
  cameras: Camera[];
}

export interface AnalysisResults {
  updated_at: string;
  resorts: Resort[];
}
