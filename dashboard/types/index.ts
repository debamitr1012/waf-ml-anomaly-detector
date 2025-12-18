export interface Statistics {
  analyzer: {
    total_analyzed: number;
    anomalies_detected: number;
    avg_latency_ms: number;
  };
  metrics: {
    requests_per_minute: number;
    detection_rate_percent: number;
    false_positive_rate_percent: number;
    uptime_seconds: number;
    attack_types: Record<string, number>;
  };
}

export interface AnalysisResult {
  request_id: string;
  is_anomaly: boolean;
  anomaly_score: number;
  confidence: number;
  attack_type: string;
  severity: string;
  timestamp: string;
  latency_ms: number;
  explanation: {
    summary: string;
    top_features: Array<{ feature: string; importance: number }>;
  };
  request_data?: {
    method: string;
    url: string;
    client_ip: string;
  };
}

export interface SecurityRule {
  id: string;
  rule_id: string;
  attack_type: string;
  severity: string;
  confidence: number;
  description: string;
  created_at: string;
  formats?: {
    modsecurity: string;
    nginx: string;
    generic: string;
  };
}

export interface RuleGenerationRequest {
  confidence_threshold?: number;
  max_rules?: number;
  attack_types?: string[];
}

export type ExportFormat = 'json' | 'modsecurity' | 'nginx';

export interface ChartDataPoint {
  time: string;
  anomalies: number;
  total: number;
}
