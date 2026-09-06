export interface Dataset {
  id: string;
  name: string;
  query: string;
  source: string | null;
  created_at: string;
  records_count: number;
}

export interface DatasetCreate {
  name: string;
  query: string;
}

export interface AuditRun {
  id: string;
  endpoint: string;
  method: string;
  status_code: number;
  duration_ms: number;
  created_at: string;
  request_body: Record<string, unknown> | null;
  response_summary: string | null;
  error: string | null;
}

export interface CollectionPlan {
  source: string;
  api_url: string;
  fields_to_keep: string[];
  filters: { [key: string]: unknown };
  confidence: "high" | "medium" | "low";
  needs_review: boolean;
  plan_steps: string[];
}

export interface AgentRun {
  id: string;
  dataset_id: string;
  plan: CollectionPlan;
  created_at: string;
}

export interface PlanResponse {
  agent_run_id: string;
  plan: CollectionPlan;
}

export interface CollectResponse {
  dataset_id: string;
  records_saved: number;
  source: string;
}

export interface DataRecord {
  id: string;
  source: string;
  collected_at: string;
  data: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string;
  records_used: number;
  needs_review: boolean;
  review_reason: string | null;
}
