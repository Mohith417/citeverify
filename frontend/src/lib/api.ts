import axios from "axios";
import type {
  ClaimDetail,
  DocumentInfo,
  DocumentResults,
  DocumentStatus,
  Health,
  Verdict,
  Verification,
} from "./types";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  timeout: 60000,
});

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg as string;
    if (error.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!error.response) return "Cannot reach the CiteVerify API. Is the backend running on port 8000?";
  }
  return "Something went wrong. Please try again.";
}

export { errorMessage };

export const api = {
  health: () => client.get<Health>("/api/health").then((r) => r.data),

  listDocuments: () => client.get<DocumentInfo[]>("/api/documents").then((r) => r.data),

  upload: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return client
      .post<DocumentInfo>("/api/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            onProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      })
      .then((r) => r.data);
  },

  analyze: (id: string) =>
    client.post<DocumentStatus>(`/api/documents/${id}/analyze`).then((r) => r.data),

  status: (id: string) =>
    client.get<DocumentStatus>(`/api/documents/${id}/status`).then((r) => r.data),

  results: (id: string) =>
    client.get<DocumentResults>(`/api/documents/${id}/results`).then((r) => r.data),

  claim: (claimId: string) =>
    client.get<ClaimDetail>(`/api/claims/${claimId}`).then((r) => r.data),

  review: (claimId: string, body: { action: "confirmed" | "overridden" | "note"; new_verdict?: Verdict; note?: string }) =>
    client.post<Verification>(`/api/claims/${claimId}/review`, body).then((r) => r.data),

  deleteDocument: (id: string) =>
    client.delete(`/api/documents/${id}`).then((r) => r.data),

  reportUrl: (id: string) => `${import.meta.env.VITE_API_URL || ""}/api/documents/${id}/report`,
};
