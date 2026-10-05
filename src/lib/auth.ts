const KEY = "insureai.token";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEY);
}

export function clearToken(): void {
  if (typeof window !== "undefined") localStorage.removeItem(KEY);
}

/**
 * Dev auth: auto-mints an officer JWT via the backend's dev-only endpoint.
 * SWAP POINT for Keycloak/OIDC: replace this function with an authorization-
 * code redirect flow. Nothing else in the app touches tokens.
 */
export async function ensureToken(): Promise<string> {
  const existing = getToken();
  if (existing) return existing;
  const res = await fetch(`${API_URL}/auth/dev-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sub: "musa-rioba", roles: ["officer"] }),
  });
  if (!res.ok) throw new Error("auth unavailable — is the API running with ENVIRONMENT=dev?");
  const data = (await res.json()) as { access_token: string };
  localStorage.setItem(KEY, data.access_token);
  return data.access_token;
}