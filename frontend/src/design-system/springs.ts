import type { Transition } from "framer-motion";

export const SPRING_SNAPPY: Transition = { type: "spring", stiffness: 320, damping: 28, mass: 0.8 };
export const SPRING_FLUID: Transition = { type: "spring", stiffness: 110, damping: 22, mass: 1 };
export const SPRING_GENTLE: Transition = { type: "spring", stiffness: 60, damping: 18, mass: 1.2 };
export const SPRING_BOUNCY: Transition = { type: "spring", stiffness: 400, damping: 22, mass: 0.6 };

export const EASE_EXPO_OUT = [0.16, 1, 0.3, 1] as const;
export const EASE_QUART_OUT = [0.25, 1, 0.5, 1] as const;
export const EASE_SUBTLE = [0.4, 0, 0.2, 1] as const;

export const STAGGER_FAST = 0.04;
export const STAGGER_MED = 0.07;
export const STAGGER_SLOW = 0.12;

export const DURATION_FAST = 0.16;
export const DURATION_BASE = 0.24;
export const DURATION_SLOW = 0.42;
