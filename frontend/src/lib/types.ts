// Mirrors the backend Pydantic DTOs. Keep in sync with backend/app/schemas.

export type ProcessingState =
  | "IDLE"
  | "UPLOADING"
  | "UPLOADED"
  | "ANALYZING"
  | "ANALYZED"
  | "REVIEWING"
  | "FORMATTING"
  | "FORMATTED"
  | "VALIDATING"
  | "VALIDATED"
  | "EXPORTING"
  | "EXPORTED"
  | "ERROR";

export interface HealthResponse {
  status: string;
  version: string;
  capabilities: { pdf_export: boolean };
}

export interface ProfileSummary {
  id: string;
  name: string;
  summary: string;
  features: string[];
  status: "available" | "planned";
}

export interface DocumentOut {
  id: string;
  filename: string;
  size: number;
  state: string;
  created_at: string;
}

export interface StageOut {
  key: string;
  label: string;
  status: "pending" | "active" | "done";
  detail: string;
}

export interface StatsOut {
  words: number;
  paragraphs: number;
  headings: number;
  tables: number;
  figures: number;
  references: number;
  sections: number;
}

export interface FieldOut {
  value: string;
  confidence: number;
  edited_by_user: boolean;
  source_index: number | null;
}

export interface AuthorOut {
  name: string;
  email: string | null;
  affiliation_ids: string[];
}

export interface AuthorsFieldOut {
  value: AuthorOut[];
  confidence: number;
  edited_by_user: boolean;
}

export interface KeywordsFieldOut {
  value: string[];
  confidence: number;
  edited_by_user: boolean;
}

export interface AffiliationOut {
  id: string;
  text: string;
}

export interface MetadataOut {
  title: FieldOut;
  authors: AuthorsFieldOut;
  affiliations: AffiliationOut[];
  abstract: FieldOut;
  keywords: KeywordsFieldOut;
}

export interface MetadataIn {
  title?: string;
  authors?: { name: string; email?: string | null; affiliation_ids?: string[] }[];
  affiliations?: { id?: string | null; text: string }[];
  abstract?: string;
  keywords?: string[];
}

export type Severity = "error" | "warning" | "info";

export interface IssueOut {
  id: string;
  severity: Severity;
  category: string;
  message: string;
  location: string | null;
  suggested_action: string | null;
}

export interface AnalysisOut {
  state: string;
  stages: StageOut[];
  stats: StatsOut | null;
  metadata: MetadataOut | null;
  parse_warnings: string[];
  issues: IssueOut[];
  error: string | null;
  profile_id: string | null;
  health: HealthScoreOut | null;
  change_log: ChangeLogOut | null;
  preservation: PreservationOut | null;
}

export interface ElementOut {
  id: string;
  kind: string;
  confidence: number;
  text_preview: string;
  needs_review: boolean;
  level: number | null;
  number: number | null;
  section: string | null;
}

export interface ElementPage {
  items: ElementOut[];
  total: number;
  offset: number;
  limit: number;
}

export interface OutlineNode {
  id: string;
  label: string;
  level: number;
  block_id: string | null;
  canonical: string | null;
  children: OutlineNode[];
}

export interface OutlineOut {
  nodes: OutlineNode[];
}

export interface HealthContributorOut {
  category: string;
  delta: number;
  reason: string;
}

export interface HealthScoreOut {
  total: number;
  categories: Record<string, number>;
  contributors: HealthContributorOut[];
}

export interface PreservationOut {
  passed: boolean;
  paragraph_delta: number;
  text_match: boolean;
  details: string[];
}

export interface ChangeLogOut {
  formatting_changes: string[];
  content_changes: string[];
  warnings_remaining: number;
}

export interface FormatOut {
  state: string;
  profile_id: string;
  change_log: ChangeLogOut;
  health: HealthScoreOut;
  issues: IssueOut[];
  preservation: PreservationOut;
}

export interface ValidateOut {
  state: string;
  issues: IssueOut[];
  health: HealthScoreOut;
  preservation: PreservationOut;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  detail?: unknown;
  hint?: string;
  error_id?: string;
}
