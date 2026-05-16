import { useMotionValue, useSpring, type MotionValue } from "framer-motion";
import { useCallback, useRef } from "react";

interface MagneticHover {
  ref: (node: HTMLElement | null) => void;
  x: MotionValue<number>;
  y: MotionValue<number>;
  onPointerMove: (event: React.PointerEvent<HTMLElement>) => void;
  onPointerLeave: () => void;
}

export function useMagneticHover(strength = 0.32): MagneticHover {
  const elementRef = useRef<HTMLElement | null>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 240, damping: 18, mass: 0.4 });
  const springY = useSpring(y, { stiffness: 240, damping: 18, mass: 0.4 });

  const ref = useCallback((node: HTMLElement | null) => {
    elementRef.current = node;
  }, []);

  const onPointerMove = useCallback(
    (event: React.PointerEvent<HTMLElement>) => {
      const node = elementRef.current;
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const relX = event.clientX - (rect.left + rect.width / 2);
      const relY = event.clientY - (rect.top + rect.height / 2);
      x.set(relX * strength);
      y.set(relY * strength);
    },
    [strength, x, y],
  );

  const onPointerLeave = useCallback(() => {
    x.set(0);
    y.set(0);
  }, [x, y]);

  return { ref, x: springX, y: springY, onPointerMove, onPointerLeave };
}
