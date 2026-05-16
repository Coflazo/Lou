import { Lock } from "@phosphor-icons/react";
import { useRoleGate } from "@/hooks/useAuth";
import { EmptyState } from "./EmptyState";
import type { Role } from "@/types";

interface RoleGateProps {
  required: Role;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGate({ required, children, fallback }: RoleGateProps) {
  const allowed = useRoleGate(required);
  if (allowed) return <>{children}</>;
  if (fallback) return <>{fallback}</>;
  return (
    <EmptyState
      icon={<Lock size={24} />}
      title={`${required} access required`}
      body="Switch to a higher role from the sidebar to view this workspace."
    />
  );
}
