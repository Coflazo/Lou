export const APP = {
  NAME: "Lou",
  TAGLINE: "Know every position.",
  DESCRIPTION:
    "A workspace for legal teams to read contracts, route exceptions, and keep negotiation positions current.",
} as const;

export const COPY = {
  LOGIN: {
    TITLE: "Lou",
    SUBTITLE: "Pick a role to begin.",
    ROLE_JUNIOR: {
      title: "Junior counsel",
      body: "Read contracts, surface unmapped clauses, propose updates for review.",
    },
    ROLE_SENIOR: {
      title: "Senior counsel",
      body: "Approve or reject proposals, edit positions, publish to the playbook.",
    },
    ROLE_ADMIN: {
      title: "Legal operations",
      body: "Configure playbooks, manage the company brain, govern integrations.",
    },
    SUBMIT: "Enter workspace",
  },
  NAV: {
    DASHBOARD: "Overview",
    PLAYBOOKS: "Playbooks",
    CONTRACTS: "Contracts",
    REVIEW: "Review queue",
    VOICE: "Voice session",
    BRAIN: "Company brain",
    EXPORTS: "Exports",
  },
  PLAYBOOKS: {
    LIST_TITLE: "Playbooks",
    LIST_SUBTITLE: "Negotiation positions, fallback ladders, and red lines per category.",
    EMPTY: "No playbooks yet. Import a workbook to begin.",
    DETAIL_SUBTITLE: "Topic-level positions, with edit history and the live knowledge graph.",
    EDIT_GATE: "Editing requires senior counsel.",
    EDIT_HINT: "Inline edits save directly to the active playbook.",
  },
  CONTRACTS: {
    LIST_TITLE: "Contracts",
    LIST_SUBTITLE: "Uploaded documents and the findings Lou produced from each.",
    UPLOAD_TITLE: "New contract",
    UPLOAD_PROMPT: "Drop a PDF or DOCX. Lou will detect sections, map clauses, and score risk.",
    UPLOAD_CTA: "Run review",
    ANALYZING: "Reading the document",
    EMPTY: "No contracts yet. Upload one to see findings appear here.",
  },
  ANALYSIS: {
    DOCUMENT_LABEL: "Document",
    FINDINGS_LABEL: "Findings",
    SECTIONS_LABEL: "Sections",
    RISK_LABEL: "Risk posture",
    NO_FINDINGS: "Lou could not find clauses against this playbook.",
  },
  REVIEW: {
    QUEUE_TITLE: "Review queue",
    QUEUE_SUBTITLE: "Proposals waiting on senior counsel approval.",
    EMPTY: "Inbox is clear. Submitted proposals will show up here.",
    APPROVE: "Approve",
    REJECT: "Reject",
    APPROVED: "Approved. The playbook version moved forward.",
    REJECTED: "Rejected. The proposal will not commit.",
    SHORTCUTS: "Use A to approve, R to reject.",
  },
  VOICE: {
    TITLE: "Voice session",
    SUBTITLE: "Capture decisions as they happen. Lou turns transcripts into review-ready suggestions.",
    START: "Start listening",
    STOP: "Stop session",
    LISTENING: "Listening",
    IDLE: "Idle. Press start.",
    PROCESSING: "Aligning to playbook",
    NO_MATCHES: "No proposals were strong enough to capture from this transcript.",
    TRANSCRIPT_FALLBACK: "Or paste a transcript directly.",
    LANGUAGE_LABEL: "Language",
  },
  BRAIN: {
    TITLE: "Company brain",
    SUBTITLE: "A simple mind map of legal teams, policies, vendors, and clauses.",
    SEARCH_PLACEHOLDER: "Search the mind map",
    LEGEND_ROOT: "Root: company legal memory",
    LEGEND_BRANCH: "Branches: entity groups",
    LEGEND_LEAF: "Leaves: teams, policies, vendors, and clauses",
  },
  EXPORT: {
    TITLE: "Exports",
    SUBTITLE: "Download a snapshot of the playbook and ongoing review.",
    JSON_BODY: "Machine-readable playbooks, proposals, commits.",
    XLSX_BODY: "Spreadsheet view of every position across categories.",
    PNG_BODY: "Image of the current company brain.",
  },
  ERRORS: {
    GENERIC: "Something went wrong. Try again in a moment.",
    UNAUTHORIZED: "Your role does not have access to this view.",
    NOT_FOUND: "We could not find what you were looking for.",
    UPLOAD_FAIL: "Upload failed. Make sure the document is a text-based PDF or DOCX.",
  },
} as const;

export const ROLES = ["JUNIOR", "SENIOR", "ADMIN"] as const;

export const TOAST_DURATION_MS = 4200;
export const SIDEBAR_WIDTH_PX = 240;
export const SIDEBAR_DRAWER_WIDTH_PX = 288;
export const MOBILE_BREAKPOINT_PX = 768;
export const VOICE_LANGUAGES = ["en", "fr", "nl", "de"] as const;
export const DEMO_TRANSCRIPT_FALLBACK =
  "Partner insists residual knowledge carve-out should be acceptable if it excludes source code and pricing.";
export const ALGORITHM_BADGES = [
  "Bayesian risk",
  "HMM section detection",
  "TF-IDF clause match",
] as const;
export const CONTRACT_ACCEPT_MIME: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
};
export const GRAPH_BRANCH_COLORS = [
  "var(--color-amber)",
  "var(--color-green)",
  "var(--color-red)",
  "var(--color-ink)",
  "var(--color-warm-gray)",
] as const;
export const GRAPH_DEFAULT_WIDTH_PX = 760;
export const GRAPH_DEFAULT_HEIGHT_PX = 520;
export const WAVEFORM_BARS = 56;
export const VOICE_ORB_SIZE_PX = 160;
