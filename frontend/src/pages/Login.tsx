import { motion, AnimatePresence } from "framer-motion";
import { ArrowUpRight } from "@phosphor-icons/react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ALGORITHM_BADGES, COPY, ROLES } from "@/lib/constants";
import { useLogin } from "@/hooks/useApi";
import { useCurrentRole, useSetRole } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

const ROLE_COPY: Record<Role, { title: string; body: string }> = {
  JUNIOR: COPY.LOGIN.ROLE_JUNIOR,
  SENIOR: COPY.LOGIN.ROLE_SENIOR,
  ADMIN: COPY.LOGIN.ROLE_ADMIN,
};

export function LoginPage() {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState<Role | null>(null);
  const role = useCurrentRole();
  const setRole = useSetRole();
  const login = useLogin();

  async function handleEnter(target: Role) {
    setRole(target);
    await login.mutateAsync(target);
    navigate("/dashboard");
  }

  return (
    <div className="min-h-screen bg-ink text-paper grid lg:grid-cols-[1fr_minmax(420px,1fr)]">
      <section className="relative overflow-hidden flex flex-col justify-between p-12 lg:p-16">
        <motion.span
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs uppercase tracking-[0.3em] text-[color:var(--color-amber)]"
        >
          Legal workspace
        </motion.span>

        <div className="flex flex-col gap-6 max-w-lg">
          <motion.h1
            initial={{ clipPath: "inset(0 100% 0 0)", opacity: 0 }}
            animate={{ clipPath: "inset(0 0% 0 0)", opacity: 1 }}
            transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] }}
            className="w-fit"
          >
            <img src="/lou-wordmark-on-dark.png" alt="Lou" className="h-20 w-auto" />
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="text-2xl text-[color:oklch(82%_0.008_88)] max-w-md font-display"
          >
            Read every contract. Route every exception. Keep every negotiation position current.
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-base text-[color:var(--color-warm-gray)] max-w-sm"
          >
            Tap a role to enter the workspace. You can switch any time from the sidebar.
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="font-mono text-xs uppercase tracking-[0.2em] text-[color:var(--color-warm-gray)] flex flex-wrap gap-x-4 gap-y-1"
        >
          {ALGORITHM_BADGES.map((badge, index) => (
            <span key={badge} className="flex items-center gap-4">
              {index > 0 && <span>·</span>}
              <span>{badge}</span>
            </span>
          ))}
        </motion.div>
      </section>

      <section className="bg-surface-base text-ink p-12 lg:p-16 flex flex-col justify-center gap-6">
        <div className="flex flex-col gap-1">
          <span className="eyebrow">Select role</span>
          <h2 className="text-3xl">{COPY.LOGIN.SUBTITLE}</h2>
        </div>

        <div className="flex flex-col gap-3">
          {ROLES.map((option, index) => {
            const meta = ROLE_COPY[option];
            const isActive = option === role;
            return (
              <motion.button
                key={option}
                onClick={() => setRole(option)}
                onMouseEnter={() => setHovered(option)}
                onMouseLeave={() => setHovered(null)}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "group relative text-left rounded-[16px] border border-[color:var(--border-soft)] bg-surface-raised px-5 py-4 flex items-start justify-between gap-4 transition-colors",
                  isActive && "border-[color:var(--color-amber)] shadow-[var(--shadow-2)]",
                )}
              >
                <div className="flex flex-col gap-1">
                  <span className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">{option}</span>
                  <span className="text-xl text-ink">{meta.title}</span>
                  <span className="text-base text-[color:var(--color-ink-soft)] max-w-sm">{meta.body}</span>
                </div>
                <AnimatePresence>
                  {(isActive || hovered === option) && (
                    <motion.span
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 4 }}
                      className="text-[color:var(--color-amber)] mt-1"
                    >
                      <ArrowUpRight size={18} weight="bold" />
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            );
          })}
        </div>

        <motion.button
          onClick={() => handleEnter(role)}
          whileTap={{ scale: 0.98 }}
          className="self-start inline-flex items-center gap-2 mt-3 px-6 py-3 rounded-[12px] bg-ink text-paper text-md transition-colors hover:bg-[color:var(--color-ink-soft)]"
        >
          {login.isPending ? "Entering" : COPY.LOGIN.SUBMIT}
          <ArrowUpRight size={14} />
        </motion.button>
      </section>
    </div>
  );
}
