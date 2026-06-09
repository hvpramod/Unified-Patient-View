const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Resolve the best auth token available:
 *  1. Token explicitly passed by the caller (MSAL flow)
 *  2. Demo token injected on window (dev/demo mode — no Azure AD needed)
 *  3. Empty string (gateway will return 403 unless dev mode is active)
 */
function resolveToken(token: string): string {
  if (token) return token;
  if (typeof window !== "undefined" && (window as any).__UPV_DEMO_TOKEN__) {
    return (window as any).__UPV_DEMO_TOKEN__;
  }
  return "demo-token"; // fallback — accepted by gateway when AZURE_CLIENT_ID is empty
}

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${resolveToken(token)}`,
    "Content-Type": "application/json",
  };
}

export async function apiGet<T>(path: string, token: string = ""): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    headers: authHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `API error ${resp.status}`);
  }
  return resp.json();
}

export async function apiPatch<T>(path: string, token: string = "", body: object): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `API error ${resp.status}`);
  }
  return resp.json();
}

export async function apiPost<T>(path: string, token: string = "", body: object): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `API error ${resp.status}`);
  }
  return resp.json();
}
