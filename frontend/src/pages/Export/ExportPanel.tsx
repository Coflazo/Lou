import { motion } from "framer-motion";
import { DownloadSimple, FileXls, Image as ImageIcon, FileJs } from "@phosphor-icons/react";
import { PageHeader } from "@/components/layout";
import { api } from "@/lib/api";
import { COPY } from "@/lib/constants";

const CARDS = [
  { format: "json" as const, title: "JSON", icon: FileJs, body: COPY.EXPORT.JSON_BODY },
  { format: "xlsx" as const, title: "XLSX", icon: FileXls, body: COPY.EXPORT.XLSX_BODY },
  { format: "png" as const, title: "PNG", icon: ImageIcon, body: COPY.EXPORT.PNG_BODY },
];

export function ExportPanelPage() {
  return (
    <div className="flex flex-col gap-8">
      <PageHeader eyebrow="Export" title={COPY.EXPORT.TITLE} subtitle={COPY.EXPORT.SUBTITLE} />

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {CARDS.map(({ format, title, icon: Icon, body }, index) => (
          <motion.a
            key={format}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, type: "spring", stiffness: 220, damping: 22 }}
            whileHover={{ y: -3 }}
            href={api.exportUrl(format)}
            className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-6 flex flex-col gap-4 group"
          >
            <div className="flex items-center justify-between">
              <Icon size={28} weight="duotone" className="text-[color:var(--color-amber)]" />
              <DownloadSimple
                size={16}
                className="text-[color:var(--color-warm-gray)] group-hover:text-ink transition-colors"
              />
            </div>
            <h3 className="font-display text-2xl">{title}</h3>
            <p className="text-base text-[color:var(--color-warm-gray)]">{body}</p>
          </motion.a>
        ))}
      </section>
    </div>
  );
}
