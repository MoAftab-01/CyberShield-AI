import api from "./api";

export interface PasswordResponse {
  password: string;

  length: number;

  has_uppercase: boolean;

  has_lowercase: boolean;

  has_number: boolean;

  has_special_character: boolean;

  score: number;

  strength: string;

  entropy: number;

  entropy_rating: string;

  contains_dictionary_word: boolean;

  detected_dictionary_words: string[];

  contains_pattern: boolean;

  detected_patterns: string[];

  risk_score: number;

  risk_level: string;

  recommendations: string[];
}

export async function analyzePassword(password: string) {
  const response = await api.post<PasswordResponse>(
    "/password/analyze",
    {
      password,
    }
  );

  return response.data;
}