import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Check,
  FileText,
  History,
  Info,
  Quote,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo, Health } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Button, ProgressBar, Spinner, VerdictBadge } from "@/components/ui";

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

const GUARANTEES = [
  { icon: Check, label: "Abstracts are never treated as full text" },
  { icon: Quote, label: "Every verdict keeps its evidence passage" },
  { icon: ShieldCheck, label: "Findings stay open to human review" },
];

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
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="grid items-start gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
        {/* left: the job to be done */}
        <div>
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 bg-coral ring-2 ring-ink" />
            <span className="label-mono text-ink/70">New verification</span>
          </div>

          <h1 className="display mt-4 text-[40px] leading-[0.92] sm:text-[56px]">
            Verify <span className="text-violet">a&nbsp;document</span>
          </h1>

          <p className="mt-4 max-w-lg text-[14px] leading-relaxed text-ink/65">
            One text-based PDF. Every page is read, each claim is pulled out with its citation, and
            the cited paper is matched to the real publication before anything is judged.
          </p>

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
              "group relative mt-6 flex min-h-[268px] cursor-pointer flex-col items-center justify-center gap-4 border-2 border-dashed p-7 text-center transition-all duration-200",
              dragging
                ? "border-ink bg-lavender shadow-block"
                : "border-ink/50 bg-white hover:-translate-y-0.5 hover:border-ink hover:bg-lavender-soft hover:shadow-block-sm",
            ].join(" ")}
          >
            <div className="flex h-16 w-16 items-center justify-center border-2 border-ink bg-lavender transition-transform duration-300 ease-smooth group-hover:-rotate-6 group-hover:scale-105">
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
                    <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                      uploading · {progress}%
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <>
                <div className="space-y-1">
                  <p className="display text-xl">Drop a PDF here</p>
                  <p className="text-[13px] text-slate">or click to browse · max {MAX_MB} MB</p>
                </div>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {["text-based PDF", "any publisher", "never guessed"].map((chip) => (
                    <span
                      key={chip}
                      className="border border-ink/20 bg-paper px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-ink/60"
                    >
                      {chip}
                    </span>
                  ))}
                </div>
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
                No AI key configured, so verdicts will stay <strong>insufficient evidence</strong>{" "}
                for human review. Add one in{" "}
                <code className="border border-ink/20 bg-white px-1 text-[11px]">backend/.env</code>.
              </p>
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button
              size="lg"
              onClick={submit}
              disabled={!file || busy}
              className="arrow-slide min-w-[220px]"
            >
              {busy ? (
                <Spinner className="border-white/40 border-t-white" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
              {busy ? "Uploading…" : "Upload and analyze"}
            </Button>
            <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
              runs in the background · live stages
            </span>
          </div>

          <div className="mt-4 grid gap-[2px] border-2 border-ink bg-ink sm:grid-cols-3">
            {STEPS.map((step, index) => (
              <div
                key={step}
                className="group bg-paper px-3 py-2.5 transition-colors hover:bg-white"
              >
                <p className="font-mono text-[9px] tracking-[0.14em] text-violet">0{index + 1}</p>
                <p className="mt-0.5 text-[11.5px] leading-snug text-ink/70">{step}</p>
              </div>
            ))}
          </div>
        </div>

        {/* right: what comes back */}
        <aside className="relative">
          <div
            className="absolute inset-x-3 top-3 h-full border-2 border-ink bg-lavender"
            aria-hidden
          />
          <div className="relative border-2 border-ink bg-white">
            <div className="flex items-center justify-between border-b-2 border-ink px-4 py-2.5">
              <p className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-slate">
                what comes back
              </p>
              <span className="flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.1em] text-violet">
                <span className="h-1.5 w-1.5 rounded-full bg-mint ring-1 ring-ink/40" /> report
              </span>
            </div>

            <div className="space-y-3 p-4">
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-slate">
                  claim · p. 3
                </p>
                <p className="mt-1 text-[13px] font-semibold leading-snug">
                  “The method improves accuracy over the baselines.”
                </p>
              </div>

              <div className="flex items-center justify-between border-y-2 border-line py-2">
                <VerdictBadge verdict="partially_supported" size="sm" />
                <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-slate">
                  confidence · medium
                </span>
              </div>

              <div className="border-l-2 border-violet bg-lavender-soft p-2.5">
                <p className="flex gap-2 text-[11.5px] leading-relaxed text-ink/75">
                  <Quote className="mt-0.5 h-3 w-3 shrink-0 text-coral" />
                  “Gains hold on three of five datasets; two show no significant difference.”
                </p>
                <p className="mt-1.5 font-mono text-[8.5px] uppercase tracking-[0.12em] text-violet">
                  source · results §4.2 · open access
                </p>
              </div>

              <dl className="grid grid-cols-3 gap-[2px] bg-ink">
                {[
                  { v: "8", l: "research APIs" },
                  { v: "6", l: "verdicts" },
                  { v: "100%", l: "reviewable" },
                ].map((item) => (
                  <div key={item.l} className="bg-paper px-2 py-2">
                    <dt className="font-display text-lg leading-none">{item.v}</dt>
                    <dd className="mt-1 font-mono text-[8.5px] uppercase tracking-[0.1em] text-slate">
                      {item.l}
                    </dd>
                  </div>
                ))}
              </dl>

              <ul className="space-y-1.5 pt-1">
                {GUARANTEES.map(({ icon: Icon, label }) => (
                  <li key={label} className="flex items-start gap-2 text-[11.5px] text-ink/65">
                    <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet" />
                    {label}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </aside>
      </div>

      <section className="mt-12">
        <div className="flex flex-wrap items-end justify-between gap-2 border-b-2 border-ink pb-2">
          <h2 className="display text-xl">Recent verifications</h2>
          <div className="flex items-center gap-4">
            <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
              {documents.length} stored
            </span>
            <Link to="/library">
              <Button variant="ghost" size="sm">
                <History className="h-3.5 w-3.5" /> All history
              </Button>
            </Link>
          </div>
        </div>

        {loadingDocs ? (
          <div className="flex items-center gap-2 py-6 text-sm text-slate">
            <Spinner /> Loading…
          </div>
        ) : documents.length === 0 ? (
          <p className="py-6 text-[13px] text-slate">
            Nothing here yet — your first analysis will show up.
          </p>
        ) : (
          <div className="mt-3 border-2 border-ink bg-white">
            {documents.slice(0, 6).map((doc, index) => {
              const done = doc.processing_status === "completed";
              return (
                <Link
                  key={doc.id}
                  to={done ? `/documents/${doc.id}` : `/analysis/${doc.id}`}
                  className="group flex items-center justify-between gap-3 border-b-2 border-ink/10 px-4 py-3 transition-colors last:border-b-0 hover:bg-lavender-soft"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="font-mono text-[10px] text-ink/30">
                      {String(index + 1).padStart(2, "0")}
                    </span>
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
                        done
                          ? "border-emerald-700/40 bg-mint text-emerald-800"
                          : "border-ink/20 bg-paper text-slate",
                      ].join(" ")}
                    >
                      {STATUS_LABEL[doc.processing_status] ?? doc.processing_status}
                    </span>
                    <ArrowUpRight className="h-3.5 w-3.5 text-slate transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-ink" />
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
