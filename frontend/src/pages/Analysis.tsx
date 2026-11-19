import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  Check,
  Clock,
  FileText,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo, DocumentStatus } from "@/lib/types";
import { STAGES, stageIndex } from "@/lib/utils";
import { Button, Card, ProgressBar, SectionLabel } from "@/components/ui";
import { PageHeading } from "@/components/Layout";

const ACTIVE = new Set([
  "extracting",
  "searching_references",
  "retrieving_evidence",
  "comparing_claims",
  "generating_report",
]);

export function Analysis() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const started = useRef(false);
  const [status, setStatus] = useState<DocumentStatus | null>(null);
  const [doc, setDoc] = useState<DocumentInfo | null>(null);
  const [error, setError] = useState("");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .results(id)
      .then((data) => {
        if (!cancelled) setDoc(data.document);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    let timer: number | undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const next = await api.status(id);
        if (cancelled) return;
        setStatus(next);
        if (next.processing_status === "completed") {
          window.setTimeout(() => navigate(`/documents/${id}`), 900);
          return;
        }
        if (next.processing_status === "failed") return;
        timer = window.setTimeout(poll, 2200);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    };

    const boot = async () => {
      try {
        const current = await api.status(id);
        if (cancelled) return;
        setStatus(current);
        if (current.processing_status === "completed") {
          navigate(`/documents/${id}`);
          return;
        }
        if (current.processing_status === "failed") return;
        if (!ACTIVE.has(current.processing_status) && !started.current) {
          started.current = true;
          try {
            await api.analyze(id);
          } catch (err) {
            if (!cancelled) setError(errorMessage(err));
            return;
          }
        }
        timer = window.setTimeout(poll, 1200);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    };

    boot();
    const ticker = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
      window.clearInterval(ticker);
    };
  }, [id, navigate]);

  const statusCode = status?.processing_status ?? "extracting";
  const index = stageIndex(statusCode);
  const failed = statusCode === "failed";
  const done = statusCode === "completed";
  const progress = failed ? 100 : done ? 100 : ((index + 1) / STAGES.length) * 100;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Module 02 · analysis"
        title={done ? "Verification ready" : failed ? "Analysis stopped" : "Verifying your document"}
        description={
          doc
            ? `${doc.filename} · ${doc.page_count} pages`
            : "Claims, citations and sources are processed in sequence. This page reflects the backend's real stage."
        }
        actions={
          <Link to="/upload">
            <Button variant="outline" size="sm">
              <RotateCcw className="h-3.5 w-3.5" /> New document
            </Button>
          </Link>
        }
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <div className="space-y-5">
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between border-b-2 border-ink bg-ink px-5 py-3 text-white">
              <div className="flex items-center gap-2">
                <Loader2 className={`h-4 w-4 ${done || failed ? "" : "animate-spin"}`} />
                <span className="font-mono text-[10px] uppercase tracking-[0.16em]">
                  {failed ? "pipeline failed" : done ? "pipeline complete" : "pipeline running"}
                </span>
              </div>
              <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-white/60">
                <Clock className="h-3 w-3" /> {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
              </span>
            </div>
            <div className="space-y-5 p-5">
              <div className="space-y-2">
                <ProgressBar value={progress} tone={failed ? "coral" : "violet"} />
                <p className="text-[13px] text-ink/80">
                  {failed
                    ? status?.error || status?.stage_message || "The pipeline could not finish."
                    : status?.stage_message || "Starting…"}
                </p>
              </div>

              <ol className="space-y-1">
                {STAGES.map((stage, stagePosition) => {
                  const complete = done || stagePosition < index;
                  const active = !done && !failed && stagePosition === index;
                  return (
                    <li
                      key={stage.key}
                      className={[
                        "flex items-start gap-3 border-l-2 px-3 py-2.5",
                        complete ? "border-emerald-600 bg-mint/30" : active ? "border-violet bg-lavender-soft" : "border-line",
                      ].join(" ")}
                    >
                      <span
                        className={[
                          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center border",
                          complete
                            ? "border-emerald-700 bg-emerald-600 text-white"
                            : active
                              ? "border-violet bg-violet text-white"
                              : "border-ink/25 bg-white text-transparent",
                        ].join(" ")}
                      >
                        {complete ? <Check className="h-3 w-3" /> : active ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                      </span>
                      <div>
                        <p className={["text-sm font-semibold", active ? "text-violet" : complete ? "text-ink" : "text-slate"].join(" ")}>
                          {stage.label}
                        </p>
                        <p className="text-[11.5px] leading-relaxed text-slate">{stage.hint}</p>
                      </div>
                    </li>
                  );
                })}
              </ol>

              {done ? (
                <div className="flex flex-wrap items-center gap-3 border-2 border-ink bg-mint p-4">
                  <p className="text-sm font-semibold">Report ready — opening the dashboard…</p>
                  <Link to={`/documents/${id}`}>
                    <Button size="sm" variant="dark">
                      Open dashboard <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              ) : null}

              {failed ? (
                <div className="flex items-start gap-2 border-2 border-danger bg-red-50 p-4 text-sm text-danger">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-semibold">The backend reported a failure.</p>
                    <p className="mt-1 text-[12.5px] leading-relaxed">{status?.error || "Unknown error."}</p>
                  </div>
                </div>
              ) : null}

              {error ? (
                <div className="flex items-start gap-2 border-2 border-danger bg-red-50 p-4 text-sm text-danger">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <p>{error}</p>
                </div>
              ) : null}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-5">
            <SectionLabel>Document</SectionLabel>
            <div className="mt-3 flex items-start gap-2">
              <FileText className="mt-0.5 h-4 w-4 text-violet" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{doc?.filename ?? "Loading…"}</p>
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                  {doc ? `${doc.page_count} pages` : "—"} · id {id.slice(0, 8)}
                </p>
              </div>
            </div>
            <p className="mt-3 border-t border-line pt-3 text-[11.5px] leading-relaxed text-slate">
              You can leave this page; analysis continues on the server. Returning here re-attaches to the live stage.
            </p>
          </Card>

          <Card className="bg-lavender-soft p-5">
            <SectionLabel>While it runs</SectionLabel>
            <ul className="mt-3 space-y-2 text-[12px] leading-relaxed text-ink/80">
              <li>• Reference matching uses DOI first, then exact title, then title + author.</li>
              <li>• Open-access PDFs and Europe PMC XML are preferred over abstracts.</li>
              <li>• A claim with no accessible evidence is flagged, not guessed.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
