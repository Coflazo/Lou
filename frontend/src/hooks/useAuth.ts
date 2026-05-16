import { useAuthStore } from "@/stores/authStore";
import type { Role } from "@/types";

export function useCurrentRole(): Role {
  return useAuthStore((state) => state.role);
}

export function useRoleGate(required: Role): boolean {
  return useAuthStore((state) => state.canAccess(required));
}

export function useSetRole(): (role: Role) => void {
  return useAuthStore((state) => state.setRole);
}
