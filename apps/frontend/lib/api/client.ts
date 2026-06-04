import { useMsal } from "@azure/msal-react";
import { loginRequest } from "@/lib/auth/msal-config";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAccessToken(instance: any, accounts: any[]): Promise<string> {
  if (!accounts[0]) return "";
  try {
    const result = await instance.acquireTokenSilent({ ...loginRequest, account: accounts[0] });
    return result.accessToken;
  } catch {
    return "";
  }
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || "API error");
  }
  return resp.json();
}

export async function apiPatch<T>(path: string, token: string, body: object): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || "API error");
  }
  return resp.json();
}

export async function apiPost<T>(path: string, token: string, body: object): Promise<T> {
  const resp = await fetch(`${API_URL}/api/v1${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || "API error");
  }
  return resp.json();
}
