import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowUpRight, Download, FileText, ShieldCheck } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentResults } from "@/lib/types";
import { VERDICT_ORDER, formatDate, verdictMeta } from "@/lib/utils";
import { Button, Card, EmptyState, SectionLabel, Spinner, StatTile, VerdictBadge } from "@/components/ui";
import { PageHeading } from "@/components/Layout";

export function Report() {
  const { id = "" } = useParams();
  const [data, setData] = useState<DocumentResults | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .results(id)
      .then(setData)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-16 text-sm text-slate">
        <Spinner /> Preparing report…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-16">
        <EmptyState title="Report unavailable" description={error || "This document could not be loaded."} />
      </div>
    );
  }

  const { summary, claims } = data;
  const counts: Record<string, number> = {
    supported: summary.supported,
    partially_supported: summary.partially_supported,
    unsupported: summary.unsupported,
    contradictory: summary.contradictory,
    potentially_outdated: summary.potentially_outdated,
    insufficient_evidence: summary.insufficient_evidence,
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-4">
        <Link
          to={`/documents/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
        </Link>
      </div>
      <PageHeading
        eyebrow="Verification report"
        title="Download the full report"
        description="The PDF is generated on the server from the stored claims, references, evidence passages and verdicts — the same data shown here."
        actions={
          <a href={api.reportUrl(id)} target="_blank" rel="noreferrer">
            <Button size="md" variant="primary">
              <Download className="h-4 w-4" /> Download PDF
            </Button>
          </a>
        }
      />

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile value={summary.total_claims} label="Claims" hint="included in report" />
        <StatTile value={summary.references_matched} label="Matched sources" hint="with publication trace" tone="lavender" />
        <StatTile value={summary.papers_retrieved} label="Full texts" hint="open-access evidence" tone="mint" />
        <StatTile value={summary.needs_human_review} label="For review" hint="explicitly flagged" tone="coral" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card className="p-6">
          <SectionLabel>Report contents</SectionLabel>
          <ol className="mt-3 space-y-2 text-[13px] text-ink/80">
            {[
              "Document information and processing status",
              "Overall verification summary",
              "Claim-by-claim verdicts with the exact claim wording",
              "Matched publication details, DOI and source links",
              "Verbatim evidence passages with section references",
              "Confidence indicators, limitations and review flags",
            ].map((item, index) => (
              <li key={item} className="flex gap-3">
                <span className="font-mono text-[10px] text-slate">{String(index + 1).padStart(2, "0")}</span>
                {item}
              </li>
            ))}
          </ol>

          <div className="mt-6 border-t border-line pt-4">
            <SectionLabel>Verdict summary</SectionLabel>
            <div className="mt-3 flex flex-wrap gap-2">
              {VERDICT_ORDER.map((verdict) => (
                <div key={verdict} className="flex items-center gap-2 border border-line px-2 py-1">
                  <span className={`h-2 w-2 ${verdictMeta(verdict).dot}`} />
                  <span className="text-[11px]">{verdictMeta(verdict).label}</span>
                  <span className="font-mono text-[11px] text-slate">{counts[verdict] ?? 0}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 border-t border-line pt-4">
            <SectionLabel>Claims preview</SectionLabel>
            <div className="mt-2 divide-y divide-line">
              {claims.slice(0, 8).map((claim) => (
                <Link
                  key={claim.claim_id}
                  to={`/documents/${id}/claims/${claim.claim_id}`}
                  className="flex items-center justify-between gap-3 py-2 hover:bg-paper"
                >
                  <span className="line-clamp-1 text-[12px] text-ink/80">{claim.claim_text}</span>
                  <VerdictBadge verdict={claim.verdict} size="sm" />
                </Link>
              ))}
              {claims.length > 8 ? (
                <p className="pt-2 font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                  + {claims.length - 8} more in the PDF
                </p>
              ) : null}
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <SectionLabel className="flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" /> Document
            </SectionLabel>
            <p className="mt-2 break-words text-sm font-semibold">{data.document.filename}</p>
            <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.1em] text-slate">
              {data.document.page_count} pages · {formatDate(data.document.uploaded_at)}
            </p>
            <a href={api.reportUrl(id)} target="_blank" rel="noreferrer" className="mt-4 block">
              <Button className="w-full" size="md">
                <Download className="h-4 w-4" /> Download PDF
              </Button>
            </a>
            <a
              href={api.reportUrl(id)}
              target="_blank"
              rel="noreferrer"
              className="mt-2 flex items-center justify-center gap-1 text-[11px] text-slate hover:text-ink"
            >
              opens in a new tab <ArrowUpRight className="h-3 w-3" />
            </a>
          </Card>

          <Card className="bg-lavender-soft p-5">
            <ShieldCheck className="h-5 w-5" />
            <p className="mt-2 text-[12px] leading-relaxed text-ink/80">
              The report states the evidence basis for every claim. Abstract-only findings are labelled, and claims
              without accessible evidence are marked for review — never presented as verified.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
