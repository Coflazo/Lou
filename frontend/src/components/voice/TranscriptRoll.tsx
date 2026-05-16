import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface TranscriptSegment {
  id: string;
  text: string;
  speaker?: string;
  ts?: string;
}

interface TranscriptRollProps {
  segments: TranscriptSegment[];
  listening: boolean;
  className?: string;
}

export function TranscriptRoll({ segments, listening, className }: TranscriptRollProps) {
  return (
    <div className={cn("flex flex-col gap-2 overflow-y-auto", className)}>
      <AnimatePresence initial={false}>
        {segments.map((segment, index) => (
          <motion.div
            key={segment.id}
            layout
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04, type: "spring", stiffness: 240, damping: 22 }}
            className="rounded-[12px] px-4 py-3 bg-surface-raised border border-[color:var(--border-soft)]"
          >
            <div className="flex items-center justify-between mb-1 text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
              <span>{segment.speaker ?? "Counsel"}</span>
              {segment.ts && <span>{segment.ts}</span>}
            </div>
            <p className="text-base text-ink">{segment.text}</p>
          </motion.div>
        ))}
      </AnimatePresence>
      {listening && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.4, repeat: Infinity }}
          className="font-mono text-sm text-[color:var(--color-warm-gray)] pl-1"
        >
          listening…
        </motion.div>
      )}
    </div>
  );
}

export type { TranscriptSegment };
