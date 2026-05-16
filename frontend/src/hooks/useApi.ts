import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Role } from "@/types";

export const queryKeys = {
  session: ["session"] as const,
  playbooks: ["playbooks"] as const,
  playbook: (id: string) => ["playbooks", id] as const,
  playbookBrain: (id: string) => ["playbooks", id, "brain"] as const,
  contracts: ["contracts"] as const,
  contract: (id: string) => ["contracts", id] as const,
  review: ["review"] as const,
  commits: ["commits"] as const,
  companyBrain: ["company-brain"] as const,
};

export function usePlaybooks() {
  return useQuery({ queryKey: queryKeys.playbooks, queryFn: api.listPlaybooks });
}

export function usePlaybook(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.playbook(id ?? ""),
    queryFn: () => api.getPlaybook(id as string),
    enabled: Boolean(id),
  });
}

export function usePlaybookBrain(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.playbookBrain(id ?? ""),
    queryFn: () => api.playbookBrain(id as string),
    enabled: Boolean(id),
  });
}

export function useContracts() {
  return useQuery({ queryKey: queryKeys.contracts, queryFn: api.listContracts });
}

export function useContract(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.contract(id ?? ""),
    queryFn: () => api.getContract(id as string),
    enabled: Boolean(id),
  });
}

export function useReview() {
  return useQuery({ queryKey: queryKeys.review, queryFn: api.listReview });
}

export function useCommits() {
  return useQuery({ queryKey: queryKeys.commits, queryFn: api.listCommits });
}

export function useCompanyBrain() {
  return useQuery({ queryKey: queryKeys.companyBrain, queryFn: api.companyBrain });
}

export function useLogin() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (role: Role) => api.login(role),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.session });
      client.invalidateQueries({ queryKey: queryKeys.review });
      client.invalidateQueries({ queryKey: queryKeys.companyBrain });
    },
  });
}

export function useUploadContract() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.uploadContract,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.contracts });
      client.invalidateQueries({ queryKey: queryKeys.review });
    },
  });
}

export function useAnalyzeContract() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.analyzeContract,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.contracts });
      client.invalidateQueries({ queryKey: queryKeys.review });
    },
  });
}

export function useApproveProposal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, edited }: { id: string; edited?: string }) =>
      api.approveProposal(id, edited),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: queryKeys.review });
      client.invalidateQueries({ queryKey: queryKeys.commits });
    },
  });
}

export function useRejectProposal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      api.rejectProposal(id, reason),
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.review }),
  });
}

export function useCreateReviewProposal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.createReviewProposal,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.review }),
  });
}

export function useUpdatePosition() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      playbookId,
      positionId,
      columns,
    }: {
      playbookId: string;
      positionId: string;
      columns: Record<string, string>;
    }) => api.updatePosition(playbookId, positionId, columns),
    onSuccess: (_data, variables) => {
      client.invalidateQueries({ queryKey: queryKeys.playbook(variables.playbookId) });
      client.invalidateQueries({ queryKey: queryKeys.playbookBrain(variables.playbookId) });
    },
  });
}

export function useVoiceTranscript() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.voiceTranscript,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.review }),
  });
}

export function useVoiceAudioTranscript() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.voiceAudioTranscript,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.review }),
  });
}

export function useVoiceContractFromNotes() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.voiceContractFromNotes,
    onSuccess: (data) => {
      client.invalidateQueries({ queryKey: queryKeys.contracts });
      client.invalidateQueries({ queryKey: queryKeys.contract(data.contract.id) });
      client.invalidateQueries({ queryKey: queryKeys.review });
    },
  });
}

export function useCommand() {
  return useMutation({ mutationFn: api.command });
}
