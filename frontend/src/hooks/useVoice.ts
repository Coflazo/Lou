import { useCallback, useEffect, useRef, useState } from "react";

type VoiceState = "idle" | "listening" | "stopped" | "error";

interface VoiceRecorder {
  state: VoiceState;
  amplitude: number;
  error: string | null;
  blob: Blob | null;
  blobUrl: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

export function useVoiceRecorder(): VoiceRecorder {
  const [state, setState] = useState<VoiceState>("idle");
  const [amplitude, setAmplitude] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const cleanup = useCallback(() => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    analyserRef.current?.disconnect();
    analyserRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const start = useCallback(async () => {
    if (state === "listening") return;
    setError(null);
    setBlob(null);
    setBlobUrl(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      audioCtxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      const data = new Uint8Array(analyser.frequencyBinCount);

      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i += 1) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);
        setAmplitude((prev) => prev * 0.7 + Math.min(1, rms * 4) * 0.3);
        animationRef.current = requestAnimationFrame(tick);
      };
      tick();

      const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? { mimeType: "audio/webm;codecs=opus" }
        : undefined;
      const recorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const recording = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setBlob(recording);
        setBlobUrl(URL.createObjectURL(recording));
        setState("stopped");
      };
      recorder.start();
      setState("listening");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Microphone access denied.");
      setState("error");
      cleanup();
    }
  }, [cleanup, state]);

  const stop = useCallback(() => {
    mediaRecorderRef.current?.stop();
    cleanup();
    setAmplitude(0);
  }, [cleanup]);

  const reset = useCallback(() => {
    cleanup();
    setState("idle");
    setAmplitude(0);
    setBlob(null);
    setBlobUrl(null);
    setError(null);
  }, [cleanup]);

  return { state, amplitude, error, blob, blobUrl, start, stop, reset };
}
