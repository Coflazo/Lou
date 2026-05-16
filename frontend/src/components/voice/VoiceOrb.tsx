import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";
import { cn } from "@/lib/utils";

interface VoiceOrbProps {
  amplitude: number;
  active: boolean;
  className?: string;
}

export function VoiceOrb({ amplitude, active, className }: VoiceOrbProps) {
  const target = useMotionValue(active ? 1 + amplitude * 0.7 : 1);
  const scale = useSpring(target, { stiffness: 320, damping: 22, mass: 0.6 });
  const glow = useTransform(scale, (current) => 0.4 + (current - 1) * 1.6);
  const ringScale = useSpring(target, { stiffness: 220, damping: 30, mass: 1 });

  useEffect(() => {
    target.set(active ? 1 + amplitude * 0.7 : 1);
  }, [amplitude, active, target]);

  return (
    <div className={cn("relative flex items-center justify-center", className)}>
      <motion.div
        style={{ scale: ringScale, opacity: glow }}
        className="absolute h-56 w-56 rounded-full bg-[color:var(--color-amber-soft)] blur-2xl"
      />
      <motion.div
        style={{ scale }}
        className={cn(
          "h-40 w-40 rounded-full bg-gradient-to-b from-[color:var(--color-amber)] to-[color:oklch(63%_0.10_75)]",
          "shadow-[0_30px_70px_oklch(0%_0_0_/_0.25)]",
        )}
      />
      <motion.div
        animate={{ rotate: active ? 360 : 0 }}
        transition={{ duration: 24, repeat: Infinity, ease: "linear" }}
        className="absolute h-44 w-44 rounded-full border border-dashed border-[color:var(--color-amber)]"
      />
    </div>
  );
}
