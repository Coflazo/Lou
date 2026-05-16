import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Role } from "@/types";

interface AuthState {
  role: Role;
  setRole: (role: Role) => void;
  rank: () => number;
  canAccess: (required: Role) => boolean;
}

const ROLE_RANK: Record<Role, number> = { JUNIOR: 1, SENIOR: 2, ADMIN: 3 };

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      role: "JUNIOR",
      setRole: (role) => set({ role }),
      rank: () => ROLE_RANK[get().role],
      canAccess: (required) => ROLE_RANK[get().role] >= ROLE_RANK[required],
    }),
    {
      name: "lou:auth",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

export { ROLE_RANK };
