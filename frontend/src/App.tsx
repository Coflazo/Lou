import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { useEffect, useState } from "react";
import { AppRouter } from "./router";
import { api } from "@/lib/api";
import { useCurrentRole } from "@/hooks/useAuth";

export function App() {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <RoleSync />
        <AppRouter />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function RoleSync() {
  const role = useCurrentRole();
  useEffect(() => {
    api.login(role).catch(() => {});
  }, [role]);
  return null;
}
