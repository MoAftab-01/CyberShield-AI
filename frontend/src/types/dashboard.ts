export interface DashboardStats {
  securityScore: number;
  passwordsChecked: number;
  urlsScanned: number;
  threatsDetected: number;
}

export interface Activity {
  id: number;
  title: string;
  time: string;
  status: "success" | "warning" | "danger";
}

export interface PasswordDistribution {
  Weak: number;
  Medium: number;
  Strong: number;
}

export interface URLDistribution {
  Low: number;
  Medium: number;
  High: number;
}

export interface TopDomain {
  domain: string;
  count: number;
}

export interface DashboardResponse {
  stats: DashboardStats;

  passwordDistribution: PasswordDistribution;

  urlDistribution: URLDistribution;

  topDomains: TopDomain[];

  activities: Activity[];
}