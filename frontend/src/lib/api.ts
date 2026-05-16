import type {
  AnalyzeResponse,
  BrainGraph,
  CommandResponse,
  Commit,
  Contract,
  ContractListItem,
  MindMapNode,
  Playbook,
  PlaybookPosition,
  PlaybookSummary,
  Proposal,
  Role,
  VoiceSessionResponse,
  VoiceTranscriptResponse,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const isFormData = init.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: isFormData
      ? { ...(init.headers || {}) }
      : { "Content-Type": "application/json", ...(init.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || `Request failed with ${response.status}`);
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.blob()) as unknown as T;
}

export const api = {
  login: (role: Role) =>
    request<{ role: Role }>("/api/session/demo-login", {
      method: "POST",
      body: JSON.stringify({ role }),
    }),
  currentSession: () => request<{ role: Role }>("/api/session/current"),
  listPlaybooks: () => request<PlaybookSummary[]>("/api/playbooks"),
  getPlaybook: (id: string) => request<Playbook>(`/api/playbooks/${id}`),
  importPlaybooks: () => request<{ imported: number }>("/api/playbooks/import", { method: "POST" }),
  updatePosition: (playbookId: string, positionId: string, columns: Record<string, string>) =>
    request<PlaybookPosition>(`/api/playbooks/${playbookId}/positions/${positionId}`, {
      method: "PATCH",
      body: JSON.stringify({ columns }),
    }),
  playbookBrain: (id: string) => request<BrainGraph>(`/api/playbooks/${id}/brain`).then(normalizeBrainGraph),
  companyBrain: () => request<BrainGraph>("/api/company-brain").then(normalizeBrainGraph),
  listContracts: () => request<ContractListItem[]>("/api/contracts"),
  getContract: (id: string) => request<Contract>(`/api/contracts/${id}`),
  analyzeContract: (payload: { playbook_id: string; name: string; text: string }) =>
    request<AnalyzeResponse>("/api/contracts/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadContract: ({ playbook_id, file }: { playbook_id: string; file: File }) => {
    const form = new FormData();
    form.append("playbook_id", playbook_id);
    form.append("file", file);
    return request<AnalyzeResponse>("/api/contracts/upload", { method: "POST", body: form });
  },
  voiceSession: (payload: { playbook_id?: string | null; language?: string }) =>
    request<VoiceSessionResponse>("/api/voice/session", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  voiceTranscript: (payload: { playbook_id: string; transcript: string; language?: string }) =>
    request<VoiceTranscriptResponse>("/api/voice/transcript", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  voiceAudioTranscript: ({ playbook_id, language, file }: { playbook_id: string; language?: string; file: Blob }) => {
    const form = new FormData();
    form.append("playbook_id", playbook_id);
    form.append("language", language ?? "en");
    form.append("file", file, "lou-recording.webm");
    return request<VoiceTranscriptResponse>("/api/voice/transcribe-audio", { method: "POST", body: form });
  },
  listReview: () => request<Proposal[]>("/api/review"),
  approveProposal: (proposalId: string, editedText?: string | null) =>
    request<{ proposal: Proposal; commit: Commit }>(`/api/review/${proposalId}/approve`, {
      method: "POST",
      body: JSON.stringify({ edited_text: editedText ?? null }),
    }),
  rejectProposal: (proposalId: string, reason?: string | null) =>
    request<Proposal>(`/api/review/${proposalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: reason ?? null }),
    }),
  listCommits: () => request<Commit[]>("/api/commits"),
  exportUrl: (format: "json" | "xlsx" | "png") => `${API_BASE}/api/export/${format}`,
  command: (payload: { command: string; playbook_id?: string | null }) =>
    request<CommandResponse>("/api/lou-command", { method: "POST", body: JSON.stringify(payload) }),
};

function normalizeBrainGraph(graph: BrainGraph): BrainGraph {
  if (graph.tree) return graph;
  const nodes = graph.nodes ?? [];
  const edges = graph.edges ?? [];
  return {
    ...graph,
    nodes,
    edges,
    tree: buildMindMapFromNodes(nodes),
    metrics: {
      node_count: nodes.length,
      edge_count: edges.length,
      branch_count: new Set(nodes.map((node) => node.kind)).size,
      relation_count: edges.length,
      ...graph.metrics,
    },
  };
}

function buildMindMapFromNodes(nodes: BrainGraph["nodes"]): MindMapNode {
  const grouped = new Map<string, MindMapNode[]>();
  for (const node of nodes) {
    if (node.kind === "root" || node.kind === "group") continue;
    const kind = node.kind || "entity";
    const bucket = grouped.get(kind) ?? [];
    bucket.push({
      id: node.id,
      name: node.label || node.name || node.id,
      type: "leaf",
      kind,
      summary: node.summary,
      metadata: node.metadata,
    });
    grouped.set(kind, bucket);
  }

  return {
    id: "company-brain",
    name: "Company Brain",
    type: "branch",
    kind: "root",
    summary: "Legal knowledge map",
    children: Array.from(grouped.entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([kind, children]) => ({
        id: `group-${kind}`,
        name: humanGroupName(kind),
        type: "branch",
        kind: "group",
        summary: `${children.length} item${children.length === 1 ? "" : "s"}`,
        children: children.sort((left, right) => left.name.localeCompare(right.name)),
      })),
  };
}

function humanGroupName(kind: string): string {
  const label = kind
    .replace(/[-_]/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => `${word[0]?.toUpperCase() ?? ""}${word.slice(1)}`)
    .join(" ");
  if (!label) return "Entities";
  if (label.endsWith("y")) return `${label.slice(0, -1)}ies`;
  if (label.endsWith("s")) return label;
  return `${label}s`;
}

export { API_BASE, ApiError };
