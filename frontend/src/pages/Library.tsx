import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, FileText, Plus, Trash2 } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Button, EmptyState, Spinner } from "@/components/ui";
import { PageHeading } from "@/components/Layout";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Uploaded",
  extracting: "Extracting",
  searching_references: "Searching sources",
  retrieving_evidence: "Retrieving evidence",
  comparing_claims: "Comparing claims",
  generating_report: "Generating report",
  completed: "Completed",
  failed: "Failed",
  needs_review: "Needs review",
};

export function Library() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = () =>
    api
      .listDocuments()
      .then(setDocuments)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  async function remove(id: string, filename: string) {
    if (!window.confirm(`Delete “${filename}” and its verification results? This cannot be undone.`)) return;
    setDeleting(id);
    try {
      await api.deleteDocument(id);
      setDocuments((items) => items.filter((item) => item.id !== id));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Review history"
        title="Your verifications"
        description="Every uploaded document and its processing state. Reports stay available until you delete them."
        actions={
          <Link to="/upload">
            <Button size="sm">
              <Plus className="h-3.5 w-3.5" /> New analysis
            </Button>
          </Link>
        }
      />

      {error ? <p className="mt-4 border-2 border-danger bg-red-50 p-3 text-sm text-danger">{error}</p> : null}

      <div className="mt-8">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate">
            <Spinner /> Loading documents…
          </div>
        ) : documents.length === 0 ? (
          <EmptyState
            title="No documents yet"
            description="Upload a research paper or assignment to create your first evidence-backed verification report."
            action={
              <Link to="/upload">
                <Button size="sm">Upload a PDF</Button>
              </Link>
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {documents.map((doc) => {
              const done = doc.processing_status === "completed";
              return (
                <article
                  key={doc.id}
                  className="flex flex-col justify-between rounded-xl border border-line bg-white p-5 transition-all hover:border-violet/40 hover:shadow-[0_8px_24px_-16px_rgba(75,54,245,0.5)]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-start gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-lavender-soft">
                        <FileText className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <h2 className="truncate text-sm font-semibold">{doc.filename}</h2>
                        <p className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                          {formatDate(doc.uploaded_at)}
                        </p>
                      </div>
                    </div>
                    <span
                      className={[
                        "shrink-0 border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.1em]",
                        done ? "border-emerald-700/30 bg-mint text-emerald-800" : "border-ink/20 bg-paper text-slate",
                      ].join(" ")}
                    >
                      {STATUS_LABEL[doc.processing_status] ?? doc.processing_status}
                    </span>
                  </div>
                  <div className="mt-5 flex items-center justify-between border-t border-line pt-3">
                    <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                      {doc.page_count} pages · {doc.id.slice(0, 8)}
                    </span>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        aria-label={`Delete ${doc.filename}`}
                        disabled={deleting === doc.id}
                        onClick={() => remove(doc.id, doc.filename)}
                        className="text-slate transition-colors hover:text-danger disabled:opacity-40"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                      <Link
                        to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-violet hover:underline"
                      >
                        {done ? "Open report" : "View progress"} <ArrowRight className="h-3 w-3" />
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
