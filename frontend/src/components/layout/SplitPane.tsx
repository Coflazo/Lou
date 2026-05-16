import { cn } from "@/lib/utils";

type CollapseAt = "sm" | "md" | "lg" | "never";

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  leftWidth?: string;
  rightWidth?: string;
  gap?: string;
  className?: string;
  /** Stack vertically below this Tailwind breakpoint. Default "lg". */
  collapseAt?: CollapseAt;
}

const COLLAPSE_CLASS: Record<CollapseAt, string> = {
  sm: "sm:grid sm:[grid-template-columns:var(--lou-split-cols)]",
  md: "md:grid md:[grid-template-columns:var(--lou-split-cols)]",
  lg: "lg:grid lg:[grid-template-columns:var(--lou-split-cols)]",
  never: "grid [grid-template-columns:var(--lou-split-cols)]",
};

export function SplitPane({
  left,
  right,
  leftWidth = "minmax(0, 1fr)",
  rightWidth = "380px",
  gap = "24px",
  className,
  collapseAt = "lg",
}: SplitPaneProps) {
  return (
    <div
      className={cn("flex flex-col", COLLAPSE_CLASS[collapseAt], className)}
      style={{
        gap,
        ["--lou-split-cols" as string]: `${leftWidth} ${rightWidth}`,
      }}
    >
      <div className="min-w-0">{left}</div>
      <aside className="min-w-0">{right}</aside>
    </div>
  );
}
