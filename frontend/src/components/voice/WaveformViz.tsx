import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface WaveformVizProps {
  amplitude: number;
  active: boolean;
  className?: string;
}

export function WaveformViz({ amplitude, active, className }: WaveformVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const amplitudeRef = useRef(amplitude);
  const activeRef = useRef(active);
  const phaseRef = useRef(0);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    amplitudeRef.current = amplitude;
    activeRef.current = active;
  }, [amplitude, active]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.scale(dpr, dpr);

    const bars = 56;
    function draw() {
      if (!canvas || !ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const gap = 2;
      const barWidth = (w - gap * (bars - 1)) / bars;
      phaseRef.current += 0.18;
      const amp = amplitudeRef.current;
      for (let i = 0; i < bars; i += 1) {
        const localPhase = phaseRef.current - i * 0.32;
        const wave = Math.sin(localPhase) * 0.5 + 0.5;
        const decay = activeRef.current ? amp : Math.max(0, amp - 0.04);
        amplitudeRef.current = decay;
        const value = wave * decay * 0.85 + 0.05;
        const barHeight = value * h;
        const x = i * (barWidth + gap);
        const y = (h - barHeight) / 2;
        ctx.fillStyle = activeRef.current ? "var(--color-amber)" : "var(--color-warm-gray)";
        ctx.fillRect(x, y, barWidth, barHeight);
      }
      animationRef.current = requestAnimationFrame(draw);
    }

    draw();
    return () => {
      if (animationRef.current != null) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={cn("w-full h-16 rounded-[12px]", className)}
      aria-hidden
    />
  );
}
