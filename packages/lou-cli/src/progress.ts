export type ProgressOptions = {
  enabled: boolean;
  write: (text: string) => void;
};

const FRAMES = ["-", "\\", "|", "/"];

export class Progress {
  private timer: NodeJS.Timeout | undefined;
  private index = 0;

  constructor(private readonly options: ProgressOptions) {}

  start(label: string): void {
    if (!this.options.enabled) return;
    this.options.write(`${label} ...`);
    this.timer = setInterval(() => {
      this.options.write(`\r${FRAMES[this.index % FRAMES.length]} ${label} ...`);
      this.index += 1;
    }, 90);
  }

  stage(label: string): void {
    if (!this.options.enabled) return;
    this.options.write(`\r${label.padEnd(32, ".")}`);
  }

  stop(): void {
    if (!this.options.enabled) return;
    if (this.timer) clearInterval(this.timer);
    this.options.write("\r");
  }
}
