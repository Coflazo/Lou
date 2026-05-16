import { motion } from "framer-motion";
import { forwardRef, useId, useState } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, className, id, onFocus, onBlur, value, defaultValue, ...rest },
  ref,
) {
  const internalId = useId();
  const fieldId = id ?? internalId;
  const [focused, setFocused] = useState(false);
  const filled = Boolean(value) || Boolean(defaultValue) || focused;

  return (
    <div className={cn("relative flex flex-col gap-1", className)}>
      {label && (
        <motion.label
          htmlFor={fieldId}
          animate={{
            y: filled ? -2 : 8,
            scale: filled ? 0.86 : 1,
            color: focused ? "var(--color-ink)" : "var(--color-warm-gray)",
          }}
          transition={{ type: "spring", stiffness: 320, damping: 26 }}
          className="origin-left font-mono uppercase text-xs tracking-wider pointer-events-none"
        >
          {label}
        </motion.label>
      )}
      <input
        ref={ref}
        id={fieldId}
        value={value}
        defaultValue={defaultValue}
        onFocus={(e) => {
          setFocused(true);
          onFocus?.(e);
        }}
        onBlur={(e) => {
          setFocused(false);
          onBlur?.(e);
        }}
        className={cn(
          "bg-surface-sunken text-ink rounded-[10px] px-3 py-2.5 outline-none transition-all duration-200",
          "border-b-2 border-[color:var(--border-soft)]",
          "focus:border-[color:var(--color-amber)] focus:bg-surface-raised",
          error && "border-[color:var(--color-red)]",
        )}
        {...rest}
      />
      {hint && !error && <span className="text-xs text-[color:var(--color-warm-gray)]">{hint}</span>}
      {error && <span className="text-xs text-[color:var(--color-red)]">{error}</span>}
    </div>
  );
});
