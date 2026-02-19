import { getViewerToken } from "./viewer-token";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit, publicRequest = false): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  headers.set("Content-Type", "application/json");
  if (publicRequest) {
    headers.set("X-Viewer-Token", getViewerToken());
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }
  return res.json();
}

export const api = {
  get: <T>(path: string, publicRequest = false) => request<T>(path, { method: "GET" }, publicRequest),
  post: <T>(path: string, body: unknown, publicRequest = false) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }, publicRequest),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  uploadImage: async (file: File): Promise<{ url: string }> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/uploads/image`, {
      method: "POST",
      credentials: "include",
      body: form
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(body.detail ?? "Upload failed");
    }
    return res.json();
  }
};
