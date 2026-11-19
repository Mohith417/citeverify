import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileText,
  History,
  Info,
  UploadCloud,
  X,
} from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo, Health } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Button, Card, ProgressBar, SectionLabel, Spinner } from "@/components/ui";
import { PageHeading } from "@/components/Layout";

const MAX_MB = 20;

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

export function Upload() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api
      .listDocuments()
      .then(setDocuments)
      .catch(() => setDocuments([]))
      .finally(() => setLoadingDocs(false));
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  const pick = useCallback((selected: File | null) => {
    setError("");
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      return;
    }
    if (selected.size > MAX_MB * 1024 * 1024) {
      setError(`That file is ${(selected.size / (1024 * 1024)).toFixed(1)} MB. The limit is ${MAX_MB} MB.`);
      return;
    }
    if (selected.size === 0) {
      setError("That file is empty.");
      return;
    }
    setFile(selected);
  }, []);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError("");
    setProgress(0);
    try {
      const document = await api.upload(file, setProgress);
      if (document.needs_ocr) {
        navigate(`/analysis/${document.id}`);
        return;
      }
      navigate(`/analysis/${document.id}`);
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Module 01 · upload"
        title="Verify a document"
        description="Upload a text-based academic PDF. CiteVerify extracts claims, maps citations to the reference list and retrieves the cited research — it never modifies your file."
        actions={
          <Link to="/library">
            <Button variant="outline" size="sm">
              <History className="h-3.5 w-3.5" /> Review history
            </Button>
          </Link>
        }
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-5">
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              pick(event.dataTransfer.files?.[0] ?? null);
            }}
            className={[
              "relative flex min-h-[280px] cursor-pointer flex-col items-center justify-center gap-4 rounded-xl border border-dashed p-8 text-center transition-colors",
              dragging ? "border-violet bg-lavender-soft" : "border-line bg-white hover:border-violet/50 hover:bg-lavender-soft/40",
            ].join(" ")}
          >
            <div className="flex h-16 w-16 items-center justify-center border-2 border-ink bg-lavender">
              <UploadCloud className="h-7 w-7" />
            </div>
            {file ? (
              <div className="w-full max-w-sm space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <FileText className="h-4 w-4 text-violet" />
                  <p className="truncate text-sm font-semibold">{file.name}</p>
                  <button
                    type="button"
                    aria-label="Remove file"
                    className="text-slate hover:text-ink"
                    onClick={(event) => {
                      event.stopPropagation();
                      setFile(null);
                      setProgress(0);
                    }}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB · ready to upload
                </p>
                {busy ? (
                  <div className="space-y-1.5">
                    <ProgressBar value={progress} />
                    <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
                      uploading · {progress}%
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <>
                <div className="space-y-1">
                  <p className="font-display text-xl uppercase">Drop a PDF here</p>
                  <p className="text-sm text-slate">or click to browse · max {MAX_MB} MB</p>
                </div>
                <p className="max-w-sm text-[11.5px] leading-relaxed text-slate">
                  Text-based PDFs only. Scanned or image-only files are detected and reported — CiteVerify will not pretend to have read them.
                </p>
              </>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(event) => pick(event.target.files?.[0] ?? null)}
            />
          </div>

          {error ? (
            <div className="flex items-start gap-2 border-2 border-danger bg-red-50 p-3 text-sm text-danger">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{error}</p>
            </div>
          ) : null}

          {!health?.ai_configured && health ? (
            <div className="flex items-start gap-2 border-2 border-ink bg-amber/30 p-3 text-[12.5px]">
              <Info className="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                No AI provider is configured on the backend, so claims will be extracted heuristically and verdicts
                will be marked <strong>insufficient evidence</strong> for human review. Add a key in
                <code className="mx-1 bg-white px-1 font-mono text-[11px]">backend/.env</code>
                (Gemini or an OpenAI-compatible endpoint) to enable comparison.
              </p>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <Button size="lg" onClick={submit} disabled={!file || busy}>
              {busy ? <Spinner className="border-white/40 border-t-white" /> : <ArrowRight className="h-4 w-4" />}
              {busy ? "Uploading…" : "Upload and analyze"}
            </Button>
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
              analysis runs in the background · you can follow each stage
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <Card className="p-5">
            <SectionLabel>What happens next</SectionLabel>
            <ol className="mt-4 space-y-3">
              {[
                "Text and page numbers are extracted; scanned files are rejected.",
                "Claims, citation markers and the bibliography are parsed.",
                "Each cited paper is located by DOI, then title and author.",
                "Open-access full text is fetched where legally available.",
                "Claims are compared and given a verdict with the source passage.",
              ].map((step, index) => (
                <li key={step} className="flex gap-3 text-[12.5px] leading-relaxed text-ink/80">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center border border-ink bg-white font-mono text-[10px]">
                    {index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </Card>

          <Card className="bg-lavender p-5">
            <SectionLabel className="text-ink/70">Evidence basis</SectionLabel>
            <ul className="mt-3 space-y-2 text-[12.5px] leading-relaxed text-ink/80">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" /> Full-text verdicts cite a passage from the paper.
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" /> Abstract-only analysis is labelled as such.
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" /> No accessible evidence ⇒ “insufficient evidence”.
              </li>
            </ul>
          </Card>
        </div>
      </div>

      <section className="mt-14">
        <div className="flex flex-col justify-between gap-2 border-b-2 border-ink pb-3 sm:flex-row sm:items-center">
          <h2 className="font-display text-lg uppercase">Recent documents</h2>
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
            {documents.length} stored {documents.length === 1 ? "document" : "documents"}
          </p>
        </div>
        {loadingDocs ? (
          <div className="flex items-center gap-2 py-8 text-sm text-slate">
            <Spinner /> Loading documents…
          </div>
        ) : documents.length === 0 ? (
          <p className="py-8 text-sm text-slate">No documents uploaded yet. Your first analysis will appear here.</p>
        ) : (
          <div className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
            {documents.map((doc) => {
              const done = doc.processing_status === "completed";
              return (
                <div key={doc.id} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex min-w-0 items-center gap-3">
                    <FileText className="h-4 w-4 shrink-0 text-violet" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{doc.filename}</p>
                      <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                        {formatDate(doc.uploaded_at)} · {doc.page_count} pages
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={[
                        "border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.1em]",
                        done ? "border-emerald-700/30 bg-mint text-emerald-800" : "border-ink/20 bg-paper text-slate",
                      ].join(" ")}
                    >
                      {STATUS_LABEL[doc.processing_status] ?? doc.processing_status}
                    </span>
                    <Link
                      to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-violet hover:underline"
                    >
                      {done ? "Open report" : "View progress"} <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
