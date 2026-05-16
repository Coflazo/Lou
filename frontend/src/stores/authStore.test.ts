import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "./authStore";

describe("authStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ role: "JUNIOR" });
  });

  it("starts as JUNIOR and allows role transitions", () => {
    const { role, setRole } = useAuthStore.getState();
    expect(role).toBe("JUNIOR");
    setRole("ADMIN");
    expect(useAuthStore.getState().role).toBe("ADMIN");
  });

  it("enforces role rank for canAccess", () => {
    const { setRole, canAccess } = useAuthStore.getState();
    setRole("JUNIOR");
    expect(canAccess("JUNIOR")).toBe(true);
    expect(canAccess("SENIOR")).toBe(false);
    expect(canAccess("ADMIN")).toBe(false);

    setRole("SENIOR");
    expect(canAccess("SENIOR")).toBe(true);
    expect(canAccess("ADMIN")).toBe(false);

    setRole("ADMIN");
    expect(canAccess("ADMIN")).toBe(true);
  });
});
