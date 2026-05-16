import { create } from "zustand";

interface UiState {
  sidebarOpen: boolean;
  commandPaletteOpen: boolean;
  toast: { id: number; message: string } | null;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  pushToast: (message: string) => void;
  dismissToast: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  // Closed by default on mobile; the Shell opens it as a drawer on hamburger tap
  // and the sidebar is always visible at >=md regardless of this flag.
  sidebarOpen: false,
  commandPaletteOpen: false,
  toast: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  openCommandPalette: () => set({ commandPaletteOpen: true }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
  pushToast: (message) =>
    set({ toast: { id: Date.now(), message } }),
  dismissToast: () => set({ toast: null }),
}));
