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
  searching_references: "Searching",
  retrieving_evidence: "Evidence",
  comparing_claims: "Comparing",
  generating_report: "Report",
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
    if (!window.confirm(`Delete “${filename}” and its results? This cannot be undone.`)) return;
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
    <div className="mx-auto w-full max-w-4xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="History"
        title="Your verifications"
        description="Saved reports stay here until you delete them."
        actions={
          <Link to="/upload">
            <Button size="sm">
              <Plus className="h-3.5 w-3.5" /> New analysis
            </Button>
          </Link>
        }
      />

      {error ? (
        <p className="mt-4 border-2 border-danger bg-red-50 p-3 text-[12.5px] text-danger">{error}</p>
      ) : null}

      <div className="mt-6">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate">
            <Spinner /> Loading…
          </div>
        ) : documents.length === 0 ? (
          <EmptyState
            title="Nothing verified yet"
            description="Upload a paper to get your first evidence-backed report."
            action={
              <Link to="/upload">
                <Button size="sm">Upload a PDF</Button>
              </Link>
            }
          />
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => {
              const done = doc.processing_status === "completed";
              return (
                <article
                  key={doc.id}
                  className="group flex items-center justify-between gap-3 border-2 border-ink bg-white px-4 py-3.5 transition-all duration-150 hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-block-sm"
                >
                  <Link to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`} className="flex min-w-0 flex-1 items-center gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-ink bg-lavender-soft">
                      <FileText className="h-4 w-4 text-violet" />
                    </span>
                    <div className="min-w-0">
                      <h2 className="truncate text-[13.5px] font-semibold">{doc.filename}</h2>
                      <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-slate">
                        {formatDate(doc.uploaded_at)} · {doc.page_count} pages
                      </p>
                    </div>
                  </Link>
                  <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={[
                        "hidden border px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.08em] sm:inline",
                        done ? "border-emerald-700/40 bg-mint text-emerald-800" : "border-ink/20 bg-paper text-slate",
                      ].join(" ")}
                    >
                      {STATUS_LABEL[doc.processing_status] ?? doc.processing_status}
                    </span>
                    <button
                      type="button"
                      aria-label={`Delete ${doc.filename}`}
                      disabled={deleting === doc.id}
                      onClick={() => remove(doc.id, doc.filename)}
                      className="p-2 text-slate opacity-60 transition-all hover:bg-red-50 hover:text-danger group-hover:opacity-100 disabled:opacity-30"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                    <Link
                      to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`}
                      aria-label="Open"
                      className="p-2 text-slate transition-colors hover:bg-lavender-soft hover:text-violet"
                    >
                      <ArrowRight className="h-4 w-4" />
                    </Link>
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
