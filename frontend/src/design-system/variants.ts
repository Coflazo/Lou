import type { Variants } from "framer-motion";
import {
  DURATION_BASE,
  DURATION_FAST,
  EASE_EXPO_OUT,
  SPRING_FLUID,
  SPRING_SNAPPY,
  STAGGER_FAST,
} from "./springs";

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: SPRING_FLUID },
  exit: { opacity: 0, y: -8, transition: { duration: DURATION_FAST } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: DURATION_BASE } },
  exit: { opacity: 0, transition: { duration: DURATION_FAST } },
};

export const clipReveal: Variants = {
  hidden: { clipPath: "inset(0 100% 0 0)" },
  visible: { clipPath: "inset(0 0% 0 0)", transition: { duration: 0.6, ease: EASE_EXPO_OUT } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  visible: { opacity: 1, scale: 1, transition: SPRING_SNAPPY },
  exit: { opacity: 0, scale: 0.96, transition: { duration: DURATION_FAST } },
};

export const slideFromRight: Variants = {
  hidden: { x: "100%", opacity: 0 },
  visible: { x: 0, opacity: 1, transition: SPRING_FLUID },
  exit: { x: "100%", opacity: 0, transition: { duration: 0.22 } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: STAGGER_FAST,
      delayChildren: 0.04,
    },
  },
};

export const subtleHover: Variants = {
  rest: { y: 0 },
  hover: { y: -3, transition: SPRING_SNAPPY },
};
