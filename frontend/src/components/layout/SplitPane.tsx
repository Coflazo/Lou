import { cn } from "@/lib/utils";

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  leftWidth?: string;
  rightWidth?: string;
  gap?: string;
  className?: string;
}

export function SplitPane({
  left,
  right,
  leftWidth = "minmax(0, 1fr)",
  rightWidth = "380px",
  gap = "24px",
  className,
}: SplitPaneProps) {
  return (
    <div
      className={cn("grid", className)}
      style={{ gridTemplateColumns: `${leftWidth} ${rightWidth}`, gap }}
    >
      <div className="min-w-0">{left}</div>
      <aside className="min-w-0">{right}</aside>
    </div>
  );
}
