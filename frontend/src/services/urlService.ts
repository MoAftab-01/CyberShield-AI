import api from "./api";

export interface URLResponse {
  url: string;

  is_valid_url: boolean;

  uses_https: boolean;

  contains_ip_address: boolean;

  domain: string;

  url_length: number;

  suspicious_keywords: string[];

  subdomain_count: number;

  risk_score: number;

  risk_level: string;

  recommendations: string[];

  virustotal_found: boolean;

  virustotal_malicious: number;

  virustotal_suspicious: number;

  virustotal_harmless: number;

  final_risk_score: number;

  final_risk_level: string;

  confidence: number;

  analysis_summary: string[];
}

export async function analyzeURL(url: string) {
  const response = await api.post<URLResponse>(
    "/url/analyze",
    {
      url,
    }
  );

  return response.data;
}