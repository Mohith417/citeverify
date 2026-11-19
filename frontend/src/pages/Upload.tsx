import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowRight, FileText, History, Info, UploadCloud, X } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo, Health } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Button, ProgressBar, Spinner } from "@/components/ui";
import { PageHeading } from "@/components/Layout";

const MAX_MB = 20;

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

const STEPS = ["Extract claims & citations", "Retrieve cited papers", "Compare evidence"];

export function Upload() {
  const navigate = useNavigate();
  const location = useLocation();
  const incoming = useRef(false);
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

  // A PDF dropped anywhere in the app lands here already selected.
  useEffect(() => {
    if (incoming.current) return;
    const dropped = (location.state as { file?: File } | null)?.file;
    if (dropped) {
      incoming.current = true;
      pick(dropped);
    }
  }, [location.state, pick]);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError("");
    setProgress(0);
    try {
      const document = await api.upload(file, setProgress);
      navigate(`/analysis/${document.id}`);
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b-2 border-ink pb-6">
        <div className="max-w-xl">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 bg-coral ring-2 ring-ink" />
            <span className="label-mono text-ink/70">New verification</span>
          </div>
          <h1 className="display mt-4 text-[34px] leading-[0.95] sm:text-[42px]">
            Verify a document
          </h1>
          <p className="mt-3 max-w-lg text-[13.5px] leading-relaxed text-ink/65">
            One text-based PDF. Every page is read, every claim is pulled out with its citation, and
            each cited paper is matched to the real publication before anything is judged.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/method">
            <Button variant="ghost" size="sm">
              Method
            </Button>
          </Link>
          <Link to="/library">
            <Button variant="outline" size="sm">
              <History className="h-3.5 w-3.5" /> History
            </Button>
          </Link>
        </div>
      </div>

      <div className="mt-4 grid gap-[2px] border-2 border-ink bg-ink sm:grid-cols-3">
        {[
          { k: "Bibliographic APIs", v: "Crossref · OpenAlex · Europe PMC · S2" },
          { k: "Open-access text", v: "arXiv · Unpaywall · PMC · CORE" },
          { k: "Never invented", v: "Quoted passages · human review" },
        ].map((item) => (
          <div key={item.k} className="group bg-paper px-3 py-2.5 transition-colors hover:bg-white">
            <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-violet">{item.k}</p>
            <p className="mt-1 text-[11.5px] leading-snug text-ink/65">{item.v}</p>
          </div>
        ))}
      </div>

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
          "group relative mt-6 flex min-h-[280px] cursor-pointer flex-col items-center justify-center gap-4 border-2 border-dashed p-8 text-center transition-all duration-200",
          dragging
            ? "border-ink bg-lavender shadow-block"
            : "border-ink/50 bg-white hover:-translate-y-0.5 hover:border-ink hover:bg-lavender-soft hover:shadow-block-sm",
        ].join(" ")}
      >
        <div className="flex h-16 w-16 items-center justify-center border-2 border-ink bg-lavender transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105">
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
                className="text-slate transition-colors hover:text-danger"
                onClick={(event) => {
                  event.stopPropagation();
                  setFile(null);
                  setProgress(0);
                }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
              {(file.size / (1024 * 1024)).toFixed(2)} MB · ready
            </p>
            {busy ? (
              <div className="space-y-2">
                <ProgressBar value={progress} />
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">uploading · {progress}%</p>
              </div>
            ) : null}
          </div>
        ) : (
          <>
            <div className="space-y-1">
              <p className="display text-xl">Drop a PDF here</p>
              <p className="text-[13px] text-slate">or click to browse · max {MAX_MB} MB</p>
            </div>
            <p className="max-w-xs text-[11.5px] leading-relaxed text-slate">
              Text-based PDFs. Scanned files are detected, never guessed.
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
        <div className="mt-3 flex items-start gap-2 border-2 border-danger bg-red-50 p-3 text-[12.5px] text-danger">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      ) : null}

      {!health?.ai_configured && health ? (
        <div className="mt-3 flex items-start gap-2 border-2 border-ink bg-amber/30 p-3 text-[12px] leading-relaxed">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            No AI key configured, so verdicts will stay <strong>insufficient evidence</strong> for human review.
            Add one in <code className="border border-ink/20 bg-white px-1 text-[11px]">backend/.env</code>.
          </p>
        </div>
      ) : null}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Button size="lg" onClick={submit} disabled={!file || busy} className="arrow-slide">
          {busy ? <Spinner className="border-white/40 border-t-white" /> : <ArrowRight className="h-4 w-4" />}
          {busy ? "Uploading…" : "Upload and analyze"}
        </Button>
        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
          runs in background · live stages
        </span>
      </div>

      <div className="mt-6 grid gap-2 sm:grid-cols-3">
        {STEPS.map((step, index) => (
          <div
            key={step}
            className="flex items-center gap-2 border-2 border-ink/15 bg-white px-3 py-2 text-[11.5px] transition-colors hover:border-ink hover:bg-lavender-soft"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center bg-ink font-mono text-[9px] text-white">
              {index + 1}
            </span>
            {step}
          </div>
        ))}
      </div>

      <section className="mt-12">
        <div className="flex items-center justify-between border-b-2 border-ink pb-2">
          <h2 className="display text-lg">Recent</h2>
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">{documents.length} stored</span>
        </div>
        {loadingDocs ? (
          <div className="flex items-center gap-2 py-6 text-sm text-slate">
            <Spinner /> Loading…
          </div>
        ) : documents.length === 0 ? (
          <p className="py-6 text-[13px] text-slate">Nothing here yet — your first analysis will show up.</p>
        ) : (
          <div className="mt-3 divide-y-2 divide-ink/10 border-2 border-ink bg-white">
            {documents.map((doc) => {
              const done = doc.processing_status === "completed";
              return (
                <Link
                  key={doc.id}
                  to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`}
                  className="group flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-lavender-soft"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <FileText className="h-4 w-4 shrink-0 text-violet" />
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold">{doc.filename}</p>
                      <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-slate">
                        {formatDate(doc.uploaded_at)} · {doc.page_count} pages
                      </p>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span
                      className={[
                        "border px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.08em]",
                        done ? "border-emerald-700/40 bg-mint text-emerald-800" : "border-ink/20 bg-paper text-slate",
                      ].join(" ")}
                    >
                      {STATUS_LABEL[doc.processing_status] ?? doc.processing_status}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-slate transition-transform group-hover:translate-x-1 group-hover:text-ink" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
