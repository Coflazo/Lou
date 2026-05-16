export type Role = "JUNIOR" | "SENIOR" | "ADMIN";

export type RiskLevel = "Low" | "Medium" | "High";

export type FindingStatus = "mapped" | "unmapped";

export type ProposalStatus = "pending" | "approved" | "rejected";

export interface PlaybookSummary {
  id: string;
  slug: string;
  name: string;
  category: string;
  description: string;
  owner: string;
  version: number;
  position_count: number;
}

export interface PlaybookPosition {
  id: string;
  playbook_id: string;
  topic: string;
  preferred_position: string;
  fallback_position: string;
  risk: RiskLevel | string;
  keywords: string[];
  columns: Record<string, string>;
}

export interface Playbook extends Omit<PlaybookSummary, "position_count"> {
  columns: string[];
  positions: PlaybookPosition[];
}

export interface ContractFinding {
  id: string;
  contract_id: string;
  playbook_position_id: string | null;
  topic: string;
  excerpt: string;
  status: FindingStatus;
  risk: RiskLevel | string;
  location: string;
  recommendation: string;
  start: number | null;
  end: number | null;
  match_score: number | null;
  match_method: string | null;
}

export interface ContractSection {
  id: string;
  title: string;
  text: string;
  start: number;
  end: number;
}

export interface ContractHighlight {
  id: string;
  finding_id: string;
  status: FindingStatus;
  topic: string;
  start: number;
  end: number;
  excerpt: string;
  risk?: string;
}

export interface RiskPosterior {
  levels: string[];
  mean: number[];
  dominant: string;
  credible_intervals: Record<string, [number, number]>;
  effective_n: number;
  alpha_posterior: number[];
  alpha_prior: number[];
}

export interface Contract {
  id: string;
  playbook_id: string;
  name: string;
  text: string;
  findings: ContractFinding[];
  sections: ContractSection[];
  highlights: ContractHighlight[];
  risk_posterior: RiskPosterior | null;
}

export interface VoiceMatchScore {
  position_id: string;
  topic: string;
  score: number;
  jaro: number;
  tfidf: number;
  edit: number;
}

export interface Proposal {
  id: string;
  playbook_id: string;
  topic: string;
  source: string;
  proposed_text: string;
  rationale: string;
  status: ProposalStatus;
  created_by_role: Role;
  created_at: string;
  voice_match_scores: { matches: VoiceMatchScore[] } | null;
  voice_session_id: string | null;
}

export interface Commit {
  id: string;
  proposal_id: string;
  playbook_id: string;
  message: string;
  author_role: Role;
  created_at: string;
}

export interface AnalyzeResponse {
  contract: Contract;
  sections: ContractSection[];
  findings: ContractFinding[];
  highlights: ContractHighlight[];
  risk_posterior: RiskPosterior;
  proposed_updates: Proposal[];
  review_suggestions: Array<{ finding_id: string; title: string; body: string }>;
}

export interface VoiceTranscriptResponse {
  mode: string;
  language: string;
  provider?: string;
  transcript?: string;
  speaker_segments?: Array<{ speaker: string; text: string; start?: number; end?: number }>;
  proposed_updates: Proposal[];
}

export interface VoiceContractResponse extends AnalyzeResponse {
  mode: string;
  language: string;
  generated_contract: { title: string; contract_text: string };
}

export interface VoiceSessionResponse {
  provider: string;
  mode: string;
  playbook_id: string | null;
  language: string;
  supported_languages: string[];
  stt: Record<string, unknown>;
  tts: Record<string, unknown>;
  auth_note: string;
  api_key_present: boolean;
}

export interface BrainNode {
  id: string;
  name?: string;
  label: string;
  kind: string;
  type?: "branch" | "leaf";
  metadata?: Record<string, unknown>;
  x?: number;
  y?: number;
  summary?: string;
  order?: number;
  group?: string;
  risk?: string;
}

export interface BrainEdge {
  source: string;
  target: string;
  label?: string;
  weight?: number;
  kind?: string;
  strength?: number;
}

export interface MindMapNode {
  id?: string;
  name: string;
  type: "branch" | "leaf";
  kind?: string;
  summary?: string;
  metadata?: Record<string, unknown>;
  children?: MindMapNode[];
}

export interface BrainGraph {
  nodes: BrainNode[];
  edges: BrainEdge[];
  tree?: MindMapNode;
  metrics?: {
    node_count: number;
    edge_count: number;
    branch_count: number;
    relation_count: number;
  };
}

export interface ContractListItem {
  id: string;
  playbook_id: string;
  name: string;
  finding_count: number;
  risk_dominant: string | null;
}

export interface CommandResponse {
  intent: string;
  message: string;
  playbook_id?: string | null;
}
