import type {
  AnalysisOut,
  ApiErrorBody,
  DocumentOut,
  ElementOut,
  ElementPage,
  FormatOut,
  HealthResponse,
  MetadataIn,
  MetadataOut,
  OutlineOut,
  ProfileSummary,
  ValidateOut,
} from "./types";

export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly hint?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(0, "network_error", "Could not reach the ManuScript AI backend.");
  }

  if (!res.ok) {
    let body: Partial<ApiErrorBody> = {};
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      res.status,
      body.error ?? "http_error",
      body.message ?? res.statusText ?? "Request failed.",
      body.hint,
    );
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  formats: () => request<ProfileSummary[]>("/api/formats"),

  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentOut>("/api/documents/upload", { method: "POST", body: form });
  },
  getDocument: (id: string) => request<DocumentOut>(`/api/documents/${id}`),

  analyze: (id: string) =>
    request<{ id: string; state: string }>(`/api/documents/${id}/analyze`, { method: "POST" }),
  getAnalysis: (id: string) => request<AnalysisOut>(`/api/documents/${id}/analysis`),
  getOutline: (id: string) => request<OutlineOut>(`/api/documents/${id}/outline`),
  getElements: (id: string, offset = 0, limit = 500) =>
    request<ElementPage>(`/api/documents/${id}/elements?offset=${offset}&limit=${limit}`),

  putMetadata: (id: string, body: MetadataIn) =>
    request<MetadataOut>(`/api/documents/${id}/metadata`, { ...json(body), method: "PUT" }),
  patchElement: (id: string, blockId: string, body: { kind?: string; level?: number }) =>
    request<ElementOut>(`/api/documents/${id}/elements/${blockId}`, { ...json(body), method: "PATCH" }),

  format: (id: string, profileId: string) =>
    request<FormatOut>(`/api/documents/${id}/format`, json({ profile_id: profileId })),
  validate: (id: string) =>
    request<ValidateOut>(`/api/documents/${id}/validate`, { method: "POST" }),

  deleteDocument: (id: string) =>
    request<void>(`/api/documents/${id}`, { method: "DELETE" }),

  previewUrl: (id: string) => `${API_BASE}/api/documents/${id}/preview`,
  exportDocxUrl: (id: string) => `${API_BASE}/api/documents/${id}/export/docx`,
  exportPdfUrl: (id: string) => `${API_BASE}/api/documents/${id}/export/pdf`,
};
