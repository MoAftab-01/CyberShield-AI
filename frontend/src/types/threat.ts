export interface MitreTechnique {

    technique_id: string | null;

    name: string | null;

    description: string | null;

    tactic: string | null;
}

export interface GitHubAdvisory {

    ghsa_id: string | null;

    summary: string | null;

    severity: string | null;

    published_at: string | null;

    updated_at: string | null;

    url: string | null;
}

export interface Threat {

    cve: string;

    severity: string;

    risk_level: string;

    cvss: number;

    exploitability_score: number;

    impact_score: number;

    published: string;

    last_modified: string;

    status: string;

    description: string;

    weaknesses: string[];

    references: string[];

    known_exploited: boolean;

    due_date?: string;

    required_action?: string;

    vendor_project?: string;

    product?: string;

    ransomware_use?: string;

    ai_summary?: string;

    recommendations: string[];

    epss_score?: number;

    epss_percentile?: number;

    epss_date?: string;

    // ==========================
    // Threat Correlation
    // ==========================

    priority?: string;

    threat_assessment?: string;

    // ==========================
    // MITRE ATT&CK
    // ==========================

    mitre_attack: MitreTechnique[];

    // ==========================
    // GitHub Advisories
    // ==========================

    github_advisories: GitHubAdvisory[];
}