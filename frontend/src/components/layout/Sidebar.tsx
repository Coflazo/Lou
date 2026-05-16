import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  Brain,
  ChartBar,
  Files,
  Hammer,
  Headphones,
  ListChecks,
  type Icon,
} from "@phosphor-icons/react";
import { NavLink, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { COPY, ROLES } from "@/lib/constants";
import { useCurrentRole, useRoleGate, useSetRole } from "@/hooks/useAuth";
import { useUiStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

interface NavItem {
  to: string;
  label: string;
  icon: Icon;
  required?: Role;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: COPY.NAV.DASHBOARD, icon: ChartBar },
  { to: "/playbooks", label: COPY.NAV.PLAYBOOKS, icon: BookOpen },
  { to: "/contracts", label: COPY.NAV.CONTRACTS, icon: Files },
  { to: "/review", label: COPY.NAV.REVIEW, icon: ListChecks, required: "SENIOR" },
  { to: "/voice", label: COPY.NAV.VOICE, icon: Headphones },
  { to: "/brain", label: COPY.NAV.BRAIN, icon: Brain, required: "ADMIN" },
  { to: "/exports", label: COPY.NAV.EXPORTS, icon: Hammer, required: "SENIOR" },
];

interface SidebarProps {
  drawerWidth?: number;
}

function SidebarBody({ onNavigate }: { onNavigate?: () => void }) {
  const role = useCurrentRole();
  const setRole = useSetRole();
  const canAccess = useRoleGate;
  return (
    <>
      <div className="px-5 pt-6 pb-4 flex items-center gap-3">
        <motion.img
          src="/lou-wordmark-on-light.png"
          alt="Lou"
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="h-8 w-auto"
        />
      </div>

      <nav className="flex-1 px-3 py-2 flex flex-col gap-0.5" aria-label="Primary navigation">
        {NAV.map((item) => {
          if (item.required && !canAccess(item.required)) return null;
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 px-3 py-2 rounded-[10px] transition-colors duration-200 min-h-11",
                  isActive ? "bg-surface-sunken text-ink" : "text-[color:var(--color-ink-soft)] hover:bg-surface-sunken/60",
                )
              }
            >
              {({ isActive }) => (
                <motion.span
                  className="flex items-center gap-3 w-full"
                  whileHover={{ x: 3 }}
                  transition={{ type: "spring", stiffness: 320, damping: 24 }}
                >
                  <AnimatePresence>
                    {isActive && (
                      <motion.span
                        layoutId="sidebar-marker"
                        className="absolute left-1 top-2 bottom-2 w-[3px] rounded-full bg-[color:var(--color-amber)]"
                        initial={{ scaleY: 0 }}
                        animate={{ scaleY: 1 }}
                        exit={{ scaleY: 0 }}
                        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                      />
                    )}
                  </AnimatePresence>
                  <Icon size={16} weight={isActive ? "fill" : "regular"} />
                  <span className="text-base">{item.label}</span>
                </motion.span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="px-3 pb-5">
        <div className="px-2 mb-2 eyebrow">Role</div>
        <div className="grid grid-cols-3 gap-1 p-1 bg-surface-sunken rounded-[10px]">
          {ROLES.map((option) => (
            <motion.button
              key={option}
              whileTap={{ scale: 0.96 }}
              onClick={() => setRole(option)}
              className={cn(
                "relative font-mono text-xs uppercase tracking-wider py-2 rounded-[6px] transition-colors duration-200 min-h-11",
                option === role ? "text-ink" : "text-[color:var(--color-warm-gray)] hover:text-ink",
              )}
            >
              {option === role && (
                <motion.span
                  layoutId="role-pill"
                  className="absolute inset-0 bg-surface-raised rounded-[6px] shadow-[var(--shadow-1)]"
                  transition={{ type: "spring", stiffness: 360, damping: 28 }}
                />
              )}
              <span className="relative">{option}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </>
  );
}

export function Sidebar({ drawerWidth = 288 }: SidebarProps) {
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);
  const location = useLocation();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname, setSidebarOpen]);

  return (
    <>
      <aside className="hidden md:flex row-span-2 col-start-1 col-end-2 border-r border-[color:var(--border-soft)] bg-surface-raised flex-col">
        <SidebarBody />
      </aside>

      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            key="drawer"
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 280, damping: 26 }}
            style={{ width: drawerWidth }}
            className="md:hidden fixed inset-y-0 left-0 z-50 bg-surface-raised border-r border-[color:var(--border-soft)] flex flex-col"
            aria-label="Mobile navigation"
          >
            <SidebarBody onNavigate={() => setSidebarOpen(false)} />
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
