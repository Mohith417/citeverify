import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertCircle, ArrowRight, Check, Clock, Loader2, RotateCcw } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentInfo, DocumentStatus } from "@/lib/types";
import { STAGES, stageIndex } from "@/lib/utils";
import { Button, Card, ProgressBar } from "@/components/ui";
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
  const progress = failed || done ? 100 : ((index + 1) / STAGES.length) * 100;

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Analysis"
        title={done ? "Verification ready" : failed ? "Analysis stopped" : "Verifying your document"}
        description={doc ? `${doc.filename} · ${doc.page_count} pages` : undefined}
        actions={
          <Link to="/upload">
            <Button variant="ghost" size="sm">
              <RotateCcw className="h-3.5 w-3.5" /> New document
            </Button>
          </Link>
        }
      />

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b-2 border-ink bg-paper px-5 py-3">
          <span className="flex items-center gap-2 text-[11.5px] font-semibold text-ink/70">
            <Loader2 className={`h-3.5 w-3.5 ${done || failed ? "" : "animate-spin text-violet"}`} />
            {failed ? "Stopped" : done ? "Complete" : "Running"}
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-slate">
            <Clock className="h-3 w-3" /> {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
          </span>
        </div>

        <div className="p-5">
          <ProgressBar value={progress} tone={failed ? "coral" : "violet"} />
          <p className="mt-2.5 text-[12.5px] leading-relaxed text-slate">
            {failed
              ? status?.error || status?.stage_message || "The pipeline could not finish."
              : status?.stage_message || "Starting…"}
          </p>

          <ol className="mt-5 space-y-1.5">
            {STAGES.map((stage, position) => {
              const complete = done || position < index;
              const active = !done && !failed && position === index;
              return (
                <li
                  key={stage.key}
                  className={[
                    "flex items-start gap-3 border-2 px-3 py-2.5 transition-colors",
                    complete
                      ? "border-emerald-700/30 bg-mint/40"
                      : active
                        ? "border-violet bg-lavender-soft"
                        : "border-transparent",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                      complete
                        ? "bg-emerald-600 text-white"
                        : active
                          ? "bg-violet text-white"
                          : "bg-line text-transparent",
                    ].join(" ")}
                  >
                    {complete ? <Check className="h-3 w-3" /> : active ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                  </span>
                  <div>
                    <p className={["text-[13px] font-semibold", active ? "text-violet" : complete ? "text-ink" : "text-slate"].join(" ")}>
                      {stage.label}
                    </p>
                    <p className="text-[11.5px] leading-snug text-slate">{stage.hint}</p>
                  </div>
                </li>
              );
            })}
          </ol>

          {done ? (
            <div className="mt-4 flex flex-wrap items-center gap-3 border-2 border-ink bg-mint px-4 py-3">
              <p className="text-[13px] font-semibold">Report ready — opening…</p>
              <Link to={`/documents/${id}`}>
                <Button size="sm" variant="dark">
                  Open dashboard <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          ) : null}

          {failed || error ? (
            <div className="mt-4 flex items-start gap-2 border-2 border-danger bg-red-50 p-3 text-[12.5px] text-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{status?.error || error || "Unknown error."}</p>
            </div>
          ) : null}
        </div>
      </Card>

      <p className="mt-4 text-center text-[11.5px] text-slate">
        You can leave this page — analysis keeps running on the server.
      </p>
    </div>
  );
}
