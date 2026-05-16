import { AnimatePresence, motion } from "framer-motion";
import { CaretDown, Check } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface Option {
  value: string;
  label: string;
  description?: string;
}

interface SelectProps {
  label?: string;
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function Select({ label, value, options, onChange, placeholder = "Select", className }: SelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handle(event: MouseEvent) {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  const selected = options.find((option) => option.value === value);

  return (
    <div className={cn("relative flex flex-col gap-1", className)} ref={ref}>
      {label && <span className="eyebrow">{label}</span>}
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className={cn(
          "flex items-center justify-between gap-3 px-3 py-2.5 rounded-[10px] bg-surface-sunken border-b-2 transition-all",
          "border-[color:var(--border-soft)] hover:bg-surface-raised",
          open && "border-[color:var(--color-amber)]",
        )}
      >
        <span className={cn("text-base text-ink", !selected && "text-[color:var(--color-warm-gray)]")}>
          {selected ? selected.label : placeholder}
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <CaretDown size={14} />
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul
            role="listbox"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18 }}
            className="absolute top-full left-0 right-0 mt-2 z-30 bg-surface-raised rounded-[12px] border border-[color:var(--border-soft)] shadow-[var(--shadow-3)] p-1 max-h-72 overflow-auto"
          >
            {options.map((option, index) => {
              const isSelected = option.value === value;
              return (
                <motion.li
                  key={option.value}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  role="option"
                  aria-selected={isSelected}
                >
                  <button
                    type="button"
                    onClick={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-[8px] flex items-center justify-between gap-3 transition-colors",
                      isSelected ? "bg-surface-sunken" : "hover:bg-surface-sunken",
                    )}
                  >
                    <div className="flex flex-col">
                      <span className="text-base text-ink">{option.label}</span>
                      {option.description && (
                        <span className="text-xs text-[color:var(--color-warm-gray)]">{option.description}</span>
                      )}
                    </div>
                    {isSelected && <Check size={14} className="text-[color:var(--color-amber)]" />}
                  </button>
                </motion.li>
              );
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
