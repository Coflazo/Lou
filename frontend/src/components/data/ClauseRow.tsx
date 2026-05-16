import { motion } from "framer-motion";
import { RiskBadge } from "./RiskBadge";
import { cn, truncate } from "@/lib/utils";
import type { PlaybookPosition } from "@/types";

interface ClauseRowProps {
  position: PlaybookPosition;
  active?: boolean;
  onClick?: () => void;
}

export function ClauseRow({ position, active, onClick }: ClauseRowProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ x: 4 }}
      transition={{ type: "spring", stiffness: 320, damping: 24 }}
      className={cn(
        "w-full text-left flex items-center justify-between gap-4 px-4 py-3 rounded-[12px] transition-colors",
        active ? "bg-surface-sunken border border-[color:var(--color-amber)]" : "hover:bg-surface-sunken",
      )}
    >
      <div className="flex flex-col gap-1 min-w-0">
        <span className="text-md text-ink truncate">{position.topic}</span>
        <span className="text-base text-[color:var(--color-warm-gray)]">
          {truncate(position.preferred_position, 96)}
        </span>
      </div>
      <RiskBadge level={position.risk} />
    </motion.button>
  );
}
