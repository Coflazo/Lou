import { motion, type HTMLMotionProps } from "framer-motion";
import { CircleNotch } from "@phosphor-icons/react";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "ref" | "children"> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  children?: React.ReactNode;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-ink text-paper hover:bg-[color:var(--color-ink-soft)] disabled:bg-[color:var(--color-warm-gray)]",
  secondary:
    "bg-surface-raised text-ink border border-[color:var(--border-soft)] hover:border-[color:var(--border-strong)]",
  ghost: "bg-transparent text-ink hover:bg-surface-sunken",
  danger:
    "bg-[color:var(--color-red)] text-paper hover:bg-[color:oklch(40%_0.118_22)]",
};

const SIZE_STYLES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm rounded-[8px]",
  md: "h-10 px-4 text-base rounded-[10px]",
  lg: "h-12 px-6 text-md rounded-[12px]",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { children, variant = "primary", size = "md", loading, iconLeft, iconRight, className, disabled, ...rest },
  ref,
) {
  return (
    <motion.button
      ref={ref}
      whileTap={{ scale: 0.97 }}
      whileHover={{ y: -1 }}
      transition={{ type: "spring", stiffness: 360, damping: 22 }}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium tracking-tight transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-50 disabled:saturate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-amber)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-base)]",
        VARIANT_STYLES[variant],
        SIZE_STYLES[size],
        className,
      )}
      {...rest}
    >
      {loading ? <CircleNotch size={16} className="animate-spin" /> : iconLeft}
      <span>{children}</span>
      {!loading && iconRight}
    </motion.button>
  );
});
