import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Microphone, Stop } from "@phosphor-icons/react";
import { PageHeader } from "@/components/layout";
import { Button, Select, Textarea } from "@/components/primitives";
import { VoiceOrb, WaveformViz, TranscriptRoll, type TranscriptSegment } from "@/components/voice";
import { ProposalCard } from "@/components/data";
import { useCreateReviewProposal, usePlaybooks, useVoiceAudioTranscript, useVoiceContractFromNotes, useVoiceTranscript } from "@/hooks/useApi";
import { useVoiceRecorder } from "@/hooks/useVoice";
import { COPY } from "@/lib/constants";
import type { Proposal } from "@/types";

const LANGS = [
  { value: "en", label: "English" },
  { value: "fr", label: "French" },
  { value: "nl", label: "Dutch" },
  { value: "de", label: "German" },
];

export function VoiceSessionPage() {
  const playbooks = usePlaybooks();
  const transcribe = useVoiceTranscript();
  const transcribeAudio = useVoiceAudioTranscript();
  const createContract = useVoiceContractFromNotes();
  const createReviewProposal = useCreateReviewProposal();
  const recorder = useVoiceRecorder();
  const navigate = useNavigate();
  const lastTranscribedBlob = useRef<Blob | null>(null);
  const [playbookId, setPlaybookId] = useState<string>("");
  const [language, setLanguage] = useState<string>("en");
  const [transcript, setTranscript] = useState<string>(
    "Partner insists residual knowledge carve-out should be acceptable if it excludes source code and pricing.",
  );
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);

  useEffect(() => {
    if (!playbookId && playbooks.data?.[0]) setPlaybookId(playbooks.data[0].id);
  }, [playbookId, playbooks.data]);

  const orbActive = recorder.state === "listening";
  const orbAmp = useMemo(() => Math.min(1, recorder.amplitude), [recorder.amplitude]);

  async function submit() {
    if (!playbookId || !transcript.trim()) return;
    const response = await transcribe.mutateAsync({ playbook_id: playbookId, transcript, language });
    setProposals(response.proposed_updates);
    setSegments((current) => [
      ...current,
      { id: `seg-${Date.now()}`, text: transcript, speaker: "You", ts: new Date().toLocaleTimeString() },
    ]);
  }

  async function generateContractFromNotes() {
    if (!playbookId || !transcript.trim()) return;
    const response = await createContract.mutateAsync({ playbook_id: playbookId, transcript, language });
    navigate(`/contracts/${response.contract.id}`);
  }

  useEffect(() => {
    if (!playbookId || !recorder.blob || recorder.blob === lastTranscribedBlob.current) return;
    lastTranscribedBlob.current = recorder.blob;
    transcribeAudio
      .mutateAsync({ playbook_id: playbookId, language, file: recorder.blob })
      .then((response) => {
        const spokenText = response.transcript?.trim();
        if (spokenText) {
          setTranscript(spokenText);
          const speakerSegments = response.speaker_segments?.length
            ? response.speaker_segments.map((segment, index) => ({
                id: `seg-${Date.now()}-${index}`,
                text: segment.text,
                speaker: segment.speaker,
                ts: new Date().toLocaleTimeString(),
              }))
            : [{ id: `seg-${Date.now()}`, text: spokenText, speaker: "Speaker 1", ts: new Date().toLocaleTimeString() }];
          setSegments((current) => [...current, ...speakerSegments]);
        }
        setProposals(response.proposed_updates);
      })
      .catch(() => undefined);
  }, [language, playbookId, recorder.blob, transcribeAudio]);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader eyebrow="Listening mode" title={COPY.VOICE.TITLE} subtitle={COPY.VOICE.SUBTITLE} />

      <section className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6">
        <div className="rounded-[24px] bg-ink text-paper p-8 flex flex-col gap-6">
          <header className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-[color:var(--color-amber)]">
              {orbActive ? COPY.VOICE.LISTENING : COPY.VOICE.IDLE}
            </span>
            <Select
              label="Language"
              value={language}
              onChange={setLanguage}
              options={LANGS}
              className="w-40 [&_button]:bg-[color:var(--color-ink-soft)] [&_button]:text-paper"
            />
          </header>

          <div className="flex flex-col items-center gap-6 my-6">
            <VoiceOrb amplitude={orbAmp} active={orbActive} />
            <WaveformViz amplitude={orbAmp} active={orbActive} className="max-w-md" />
          </div>

          <div className="flex flex-col gap-3">
            {recorder.error && <p className="text-sm text-[color:var(--color-red)]">{recorder.error}</p>}
            {transcribeAudio.error && (
              <p className="text-sm text-[color:var(--color-red)]">
                {transcribeAudio.error instanceof Error ? transcribeAudio.error.message : "SLNG transcription failed."}
              </p>
            )}
            {createContract.error && (
              <p className="text-sm text-[color:var(--color-red)]">
                {createContract.error instanceof Error ? createContract.error.message : "Contract generation failed."}
              </p>
            )}
            <div className="flex items-center justify-center gap-3">
              {!orbActive ? (
                <Button size="lg" iconLeft={<Microphone size={16} weight="fill" />} onClick={recorder.start}>
                  {COPY.VOICE.START}
                </Button>
              ) : (
                <Button size="lg" variant="danger" iconLeft={<Stop size={16} weight="fill" />} onClick={recorder.stop}>
                  {COPY.VOICE.STOP}
                </Button>
              )}
              {recorder.blobUrl && (
                <audio controls src={recorder.blobUrl} className="rounded-[8px]" />
              )}
            </div>
            {transcribeAudio.isPending && (
              <p className="text-center text-sm text-[color:var(--color-amber)]">Transcribing with SLNG...</p>
            )}
          </div>
        </div>

        <div className="rounded-[24px] bg-surface-raised border border-[color:var(--border-soft)] p-6 flex flex-col gap-4">
          <Select
            label="Playbook"
            value={playbookId}
            onChange={setPlaybookId}
            options={
              playbooks.data?.map((playbook) => ({
                value: playbook.id,
                label: playbook.name,
                description: playbook.category,
              })) ?? []
            }
          />
          <Textarea
            label={COPY.VOICE.TRANSCRIPT_FALLBACK}
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={8}
          />
          <Button onClick={submit} loading={transcribe.isPending || transcribeAudio.isPending}>
            Create proposals
          </Button>
          <Button
            variant="secondary"
            onClick={generateContractFromNotes}
            loading={createContract.isPending}
            disabled={!transcript.trim() || !playbookId}
          >
            Generate contract from notes
          </Button>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-6">
        <aside className="rounded-[18px] bg-surface-raised border border-[color:var(--border-soft)] p-5 max-h-[60vh] overflow-y-auto">
          <h3 className="text-xl mb-3">Transcript</h3>
          <TranscriptRoll segments={segments} listening={orbActive} />
        </aside>
        <div className="flex flex-col gap-3">
          <h3 className="text-xl">Suggested proposals</h3>
          <AnimatePresence>
            {proposals.length === 0 && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-base text-[color:var(--color-warm-gray)]"
              >
                {COPY.VOICE.NO_MATCHES}
              </motion.p>
            )}
            {proposals.map((proposal) => (
              <ProposalCard
                key={proposal.id}
                proposal={proposal}
                actions={
                  <Button
                    size="sm"
                    variant="secondary"
                    loading={createReviewProposal.isPending && createReviewProposal.variables?.topic === proposal.topic}
                    onClick={() => createReviewProposal.mutate(proposal)}
                  >
                    Send to review
                  </Button>
                }
              />
            ))}
          </AnimatePresence>
        </div>
      </section>
    </div>
  );
}
