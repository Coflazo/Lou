import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

interface AnimatedNumberProps {
  value: number;
  precision?: number;
  suffix?: string;
  className?: string;
}

export function AnimatedNumber({ value, precision = 0, suffix = "", className }: AnimatedNumberProps) {
  const raw = useMotionValue(value);
  const spring = useSpring(raw, { stiffness: 80, damping: 18, mass: 1 });
  const display = useTransform(spring, (current) => `${current.toFixed(precision)}${suffix}`);

  useEffect(() => {
    raw.set(value);
  }, [value, raw]);

  return <motion.span className={className}>{display}</motion.span>;
}
