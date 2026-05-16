import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
  rounded?: string;
}

export function Skeleton({ className, width, height, rounded = "8px" }: SkeletonProps) {
  return (
    <motion.div
      style={{ width, height, borderRadius: rounded }}
      animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
      transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
      className={cn(
        "bg-[linear-gradient(110deg,var(--surface-sunken)_0%,var(--surface-raised)_50%,var(--surface-sunken)_100%)] bg-[length:200%_100%]",
        className,
      )}
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} height="12px" width={`${85 - index * 12}%`} rounded="6px" />
      ))}
    </div>
  );
}
