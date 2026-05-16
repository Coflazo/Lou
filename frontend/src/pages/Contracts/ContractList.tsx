import { motion } from "framer-motion";
import { Files, Plus } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout";
import { Button, Skeleton } from "@/components/primitives";
import { RiskBadge } from "@/components/data";
import { EmptyState } from "@/components/shared/EmptyState";
import { useContracts } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";

export function ContractListPage() {
  const contracts = useContracts();
  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow="Documents"
        title={COPY.CONTRACTS.LIST_TITLE}
        subtitle={COPY.CONTRACTS.LIST_SUBTITLE}
        actions={
          <Link to="/contracts/new">
            <Button iconLeft={<Plus size={14} />}>New contract</Button>
          </Link>
        }
      />
      {contracts.isLoading ? (
        <Skeleton height="40vh" rounded="18px" />
      ) : contracts.data && contracts.data.length > 0 ? (
        <div className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised overflow-hidden">
          <header className="hidden md:grid grid-cols-[1fr_120px_120px] px-5 py-3 text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)] border-b border-[color:var(--border-soft)]">
            <span>Document</span>
            <span>Findings</span>
            <span>Risk</span>
          </header>
          <ul className="divide-y divide-[color:var(--border-soft)]">
            {contracts.data.map((contract, index) => (
              <motion.li
                key={contract.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
              >
                <Link
                  to={`/contracts/${contract.id}`}
                  className="grid grid-cols-[1fr_auto] md:grid-cols-[1fr_120px_120px] gap-x-4 gap-y-2 px-4 md:px-5 py-4 hover:bg-surface-sunken"
                >
                  <div className="flex flex-col">
                    <span className="text-md text-ink">{contract.name}</span>
                    <span className="text-xs font-mono text-[color:var(--color-warm-gray)]">{contract.id}</span>
                  </div>
                  <RiskBadge level={contract.risk_dominant ?? "Medium"} className="md:hidden" />
                  <span className="hidden md:inline font-mono text-md">{contract.finding_count}</span>
                  <RiskBadge level={contract.risk_dominant ?? "Medium"} className="hidden md:inline-flex" />
                  <span className="md:hidden col-span-2 text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
                    {contract.finding_count} findings
                  </span>
                </Link>
              </motion.li>
            ))}
          </ul>
        </div>
      ) : (
        <EmptyState
          icon={<Files size={28} />}
          title={COPY.CONTRACTS.EMPTY}
          action={
            <Link to="/contracts/new">
              <Button iconLeft={<Plus size={14} />}>Upload first contract</Button>
            </Link>
          }
        />
      )}
    </div>
  );
}
