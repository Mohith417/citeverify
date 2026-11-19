import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  Download,
  RefreshCw,
  Search,
  Sparkles,
} from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { ClaimRow, DocumentResults, Verdict } from "@/lib/types";
import { VERDICT_META, VERDICT_ORDER, formatDate, verdictMeta } from "@/lib/utils";
import {
  Badge,
  Button,
  Card,
  ConfidenceMeter,
  EmptyState,
  Spinner,
  VerdictBadge,
} from "@/components/ui";

type Filter = "all" | "review" | Verdict;

export function Dashboard() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<DocumentResults | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [starting, setStarting] = useState(false);

  const load = () =>
    api
      .results(id)
      .then(setData)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, [id]);

  async function runAnalysis() {
    setStarting(true);
    setError("");
    try {
      await api.analyze(id);
      navigate(`/analysis/${id}`);
    } catch (err) {
      setError(errorMessage(err));
      setStarting(false);
    }
  }

  const claims = data?.claims ?? [];
  const summary = data?.summary;
  const counts: Record<string, number> = {
    supported: summary?.supported ?? 0,
    partially_supported: summary?.partially_supported ?? 0,
    unsupported: summary?.unsupported ?? 0,
    contradictory: summary?.contradictory ?? 0,
    potentially_outdated: summary?.potentially_outdated ?? 0,
    insufficient_evidence: summary?.insufficient_evidence ?? 0,
  };

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return claims.filter((claim) => {
      if (filter === "review" && !claim.needs_human_review) return false;
      if (filter !== "all" && filter !== "review" && claim.verdict !== filter) return false;
      if (!term) return true;
      return (
        claim.claim_text.toLowerCase().includes(term) ||
        (claim.source_title ?? "").toLowerCase().includes(term) ||
        claim.citation_markers.join(" ").toLowerCase().includes(term)
      );
    });
  }, [claims, filter, query]);

  if (loading) {
    return (
      <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-16 text-sm text-slate">
        <Spinner /> Loading verification results…
      </div>
    );
  }

  if (error || !data || !summary) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-16">
        <EmptyState
          title="No results available"
          description={error || "This document could not be loaded."}
          action={
            <Link to="/upload">
              <Button size="sm">Upload a document</Button>
            </Link>
          }
        />
      </div>
    );
  }

  const analysed = summary.total_claims > 0;
  const references = data.references;
  const total = Math.max(1, claims.length);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
      {/* header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Link to="/library" className="inline-flex items-center gap-1.5 text-xs font-medium text-slate hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" /> Review history
          </Link>
          <h1 className="display mt-2 truncate text-2xl sm:text-3xl">
            {data.document.filename}
          </h1>
          <p className="mt-1 text-xs text-slate">
            {data.document.page_count} {data.document.page_count === 1 ? "page" : "pages"} ·{" "}
            {formatDate(data.document.uploaded_at)} · {references.length} references parsed
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <a href={api.reportUrl(id)} target="_blank" rel="noreferrer">
            <Button size="sm" variant="dark">
              <Download className="h-3.5 w-3.5" /> Report
            </Button>
          </a>
          <Button size="sm" variant="outline" onClick={runAnalysis} disabled={starting}>
            <RefreshCw className={`h-3.5 w-3.5 ${starting ? "animate-spin" : ""}`} />
            {analysed ? "Re-run" : "Run analysis"}
          </Button>
          <Link to={`/documents/${id}/references`}>
            <Button size="sm" variant="ghost">
              References
            </Button>
          </Link>
        </div>
      </div>

      {error ? <p className="mt-4 border-2 border-danger bg-red-50 p-3 text-sm text-danger">{error}</p> : null}

      {data.document.needs_ocr ? (
        <div className="mt-4 flex items-start gap-2 border-2 border-ink bg-amber/30 p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <p>This PDF appears to be scanned. Text could not be extracted, so OCR is required before verification.</p>
        </div>
      ) : null}

      {!analysed ? (
        <div className="mt-8">
          <EmptyState
            title="Not analysed yet"
            description="Run the verification pipeline to extract claims, locate the cited research and compare the evidence."
            action={
              <Button size="sm" onClick={runAnalysis} disabled={starting}>
                {starting ? <Spinner className="border-white/40 border-t-white" /> : <Sparkles className="h-3.5 w-3.5" />}
                Run analysis
              </Button>
            }
          />
        </div>
      ) : (
        <>
          {/* summary strip */}
          <Card className="mt-6 p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="font-display text-3xl">{summary.total_claims}</span>
                <span className="text-sm text-slate">claims verified against their cited sources</span>
              </div>
              <span className="text-[11.5px] text-slate">
                {summary.needs_human_review} to review · {summary.references_matched}/{references.length} sources
                matched · {summary.total_citations} citations
              </span>
            </div>

            <div className="mt-4 flex h-3 w-full overflow-hidden border-2 border-ink bg-white">
              {VERDICT_ORDER.map((verdict) => {
                const share = ((counts[verdict] ?? 0) / total) * 100;
                return share > 0 ? (
                  <span key={verdict} className={VERDICT_META[verdict].dot} style={{ width: `${share}%` }} />
                ) : null;
              })}
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {VERDICT_ORDER.filter((verdict) => (counts[verdict] ?? 0) > 0).map((verdict) => (
                <button
                  key={verdict}
                  type="button"
                  onClick={() => setFilter(filter === verdict ? "all" : verdict)}
                  className={[
                    "inline-flex items-center gap-1.5 border-2 px-2.5 py-1 text-[11px] font-semibold transition-all",
                    filter === verdict
                      ? "border-ink bg-ink text-white"
                      : "border-ink/15 bg-white text-ink/70 hover:border-ink hover:bg-lavender-soft",
                  ].join(" ")}
                >
                  <span className={["h-1.5 w-1.5 rounded-full", VERDICT_META[verdict].dot].join(" ")} />
                  {VERDICT_META[verdict].label}
                  <span className={filter === verdict ? "text-white/70" : "text-slate"}>{counts[verdict] ?? 0}</span>
                </button>
              ))}
            </div>

          </Card>

          {/* toolbar */}
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <h2 className="display text-xl">Claims</h2>
              <Badge>{filtered.length}</Badge>
              {filter !== "all" ? (
                <button type="button" onClick={() => setFilter("all")} className="text-[11px] font-medium text-violet hover:underline">
                  clear filter
                </button>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setFilter(filter === "review" ? "all" : "review")}
                className={[
                  "border-2 px-3 py-1.5 text-[11px] font-semibold transition-all",
                  filter === "review"
                    ? "border-ink bg-ink text-white"
                    : "border-ink/15 bg-white text-slate hover:border-ink hover:text-ink",
                ].join(" ")}
              >
                Needs review only
              </button>
              <div className="flex h-9 items-center gap-2 border-2 border-ink/15 bg-white px-3 focus-within:border-ink">
                <Search className="h-3.5 w-3.5 text-slate" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search claims"
                  className="w-36 bg-transparent text-xs outline-none placeholder:text-slate/70 sm:w-48"
                />
              </div>
            </div>
          </div>

          {/* claim list */}
          <div className="mt-3 space-y-2">
            {filtered.length === 0 ? (
              <div className="border-2 border-dashed border-ink/30 bg-white/60 p-8 text-center text-sm text-slate">
                No claims match this filter.
              </div>
            ) : (
              filtered.map((claim) => (
                <ClaimItem key={claim.claim_id} claim={claim} documentId={id} index={claims.indexOf(claim) + 1} />
              ))
            )}
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-2 border-2 border-ink bg-lavender-soft px-4 py-3">
            <p className="text-[12px] text-ink/70">
              Verdicts are evidence-backed indications, not final academic judgments.
            </p>
            <Link
              to={`/documents/${id}/references`}
              className="text-xs font-semibold text-violet hover:underline"
            >
              Inspect reference matching →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

function ClaimItem({ claim, documentId, index }: { claim: ClaimRow; documentId: string; index: number }) {
  const meta = verdictMeta(claim.verdict);
  return (
    <Link
      to={`/documents/${documentId}/claims/${claim.claim_id}`}
      className="group flex items-start gap-3 border-2 border-ink bg-white p-4 transition-all duration-150 hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-block-sm"
    >
      <span className="mt-0.5 hidden w-5 shrink-0 font-mono text-[10px] text-slate sm:block">
        {String(index).padStart(2, "0")}
      </span>
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-[13.5px] font-medium leading-snug text-ink">{claim.claim_text}</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate">
          <span>p. {claim.page_number ?? "—"}</span>
          <span className="font-mono">{claim.citation_markers.length ? claim.citation_markers.join(" ") : "no citation"}</span>
          {claim.source_title ? (
            <span className="max-w-[280px] truncate">{claim.source_title}</span>
          ) : (
            <span className="text-orange-700">no source matched</span>
          )}
          {claim.needs_human_review ? (
            <span className="inline-flex items-center gap-1 text-amber-700">
              <AlertTriangle className="h-3 w-3" /> review
            </span>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <VerdictBadge verdict={claim.verdict} size="sm" />
        <ConfidenceMeter level={claim.confidence_level} className="hidden sm:flex" />
      </div>
      <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-line transition-colors group-hover:text-violet" />
    </Link>
  );
}
