import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { FileText, UploadSimple } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/layout";
import { Button, Select, Skeleton } from "@/components/primitives";
import { usePlaybooks, useUploadContract } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function ContractUploadPage() {
  const navigate = useNavigate();
  const playbooks = usePlaybooks();
  const upload = useUploadContract();
  const [playbookId, setPlaybookId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!playbookId && playbooks.data?.[0]) setPlaybookId(playbooks.data[0].id);
  }, [playbookId, playbooks.data]);

  const dropzone = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    multiple: false,
    onDrop: (files) => {
      setError(null);
      setFile(files[0] ?? null);
    },
    onDropRejected: () => setError(COPY.ERRORS.UPLOAD_FAIL),
  });

  async function submit() {
    if (!file || !playbookId) return;
    setError(null);
    try {
      const result = await upload.mutateAsync({ playbook_id: playbookId, file });
      navigate(`/contracts/${result.contract.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : COPY.ERRORS.UPLOAD_FAIL);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow="Upload"
        title={COPY.CONTRACTS.UPLOAD_TITLE}
        subtitle={COPY.CONTRACTS.UPLOAD_PROMPT}
      />

      <section className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="bg-surface-raised rounded-[20px] border border-[color:var(--border-soft)] p-6 flex flex-col gap-4"
        >
          {playbooks.isLoading ? (
            <Skeleton height="60px" />
          ) : (
            <Select
              label="Playbook"
              value={playbookId}
              onChange={setPlaybookId}
              options={
                playbooks.data?.map((playbook) => ({
                  value: playbook.id,
                  label: playbook.name,
                  description: `${playbook.category} · v${playbook.version}`,
                })) ?? []
              }
            />
          )}

          <div
            {...dropzone.getRootProps()}
            className={cn(
              "rounded-[18px] border-2 border-dashed px-8 py-12 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all",
              dropzone.isDragActive
                ? "border-[color:var(--color-amber)] bg-[color:var(--color-amber-soft)]/40"
                : "border-[color:var(--border-soft)] bg-surface-sunken/40 hover:border-[color:var(--color-amber)]",
            )}
          >
            <input {...dropzone.getInputProps()} />
            <UploadSimple size={28} weight="duotone" className="text-[color:var(--color-amber)]" />
            <p className="text-md text-ink font-display">{file ? file.name : "Drop a PDF or DOCX"}</p>
            <p className="text-base text-[color:var(--color-warm-gray)]">
              Text-based documents only. OCR is not supported yet.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
              {file ? `${(file.size / 1024).toFixed(1)} KB` : "no file selected"}
            </span>
            <Button onClick={submit} disabled={!file || !playbookId} loading={upload.isPending}>
              {COPY.CONTRACTS.UPLOAD_CTA}
            </Button>
          </div>
          {error && <p className="text-sm text-[color:var(--color-red)]">{error}</p>}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.06 }}
          className="bg-ink text-paper rounded-[20px] p-6 flex flex-col gap-4"
        >
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-[color:var(--color-amber)]">Pipeline</span>
          <h3 className="font-display text-2xl">What Lou will do.</h3>
          <ol className="flex flex-col gap-3 text-base text-[color:oklch(82%_0.008_88)]">
            <Step n={1} title="Detect sections" body="HMM Viterbi over a 7-dim feature vector per paragraph." />
            <Step n={2} title="Match clauses" body="TF-IDF cosine similarity against playbook positions." />
            <Step n={3} title="Score risk" body="Dirichlet–Categorical posterior with 95% credible intervals." />
            <Step n={4} title="Route exceptions" body="Unmapped clauses become proposals for the review queue." />
          </ol>
          <AnimatePresence>
            {upload.isPending && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-3 mt-3 text-[color:var(--color-amber)]"
              >
                <FileText size={14} className="animate-pulse" />
                <span className="text-sm font-mono uppercase tracking-wider">{COPY.CONTRACTS.ANALYZING}…</span>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </section>
    </div>
  );
}

function Step({ n, title, body }: { n: number; title: string; body: string }) {
  return (
    <li className="flex gap-3">
      <span className="flex-shrink-0 h-6 w-6 rounded-full bg-[color:var(--color-amber)] text-ink font-mono text-xs flex items-center justify-center">
        {n}
      </span>
      <div className="flex flex-col">
        <span className="text-paper">{title}</span>
        <span className="text-[color:var(--color-warm-gray)]">{body}</span>
      </div>
    </li>
  );
}
