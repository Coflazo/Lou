import { motion } from "framer-motion";
import { CheckCircle } from "@phosphor-icons/react";
import { formatRelative } from "@/lib/utils";
import type { Commit } from "@/types";

interface CommitTimelineProps {
  commits: Commit[];
}

export function CommitTimeline({ commits }: CommitTimelineProps) {
  return (
    <ol className="relative pl-6">
      <motion.span
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        style={{ transformOrigin: "top" }}
        className="absolute left-2 top-1 bottom-1 w-px bg-[color:var(--border-soft)]"
      />
      {commits.map((commit, index) => (
        <motion.li
          key={commit.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className="relative mb-5 last:mb-0"
        >
          <span className="absolute -left-[18px] top-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-surface-raised border border-[color:var(--color-green)]">
            <CheckCircle size={10} weight="fill" className="text-[color:var(--color-green)]" />
          </span>
          <p className="text-md text-ink">{commit.message}</p>
          <p className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">
            {commit.author_role} · {formatRelative(commit.created_at)}
          </p>
        </motion.li>
      ))}
      {commits.length === 0 && (
        <li className="text-base text-[color:var(--color-warm-gray)]">No commits yet.</li>
      )}
    </ol>
  );
}
