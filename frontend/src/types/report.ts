export interface PasswordReport {
  id: number;
  password_strength: string;
  entropy: number;
  score: number;
  created_at: string;
}

export interface URLReport {
  id: number;
  url: string;
  domain: string;
  uses_https: boolean;
  risk_score: number;
  risk_level: string;
  final_risk_score: number;
  final_risk_level: string;
  confidence: number;
  is_safe: boolean;
  created_at: string;
}

export interface PasswordReportResponse {
  total: number;
  page: number;
  page_size: number;
  items: PasswordReport[];
}

export interface URLReportResponse {
  total: number;
  page: number;
  page_size: number;
  items: URLReport[];
}