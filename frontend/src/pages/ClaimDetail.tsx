import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowUpRight,
  BadgeCheck,
  Check,
  ClipboardCheck,
  ExternalLink,
  FileWarning,
  Quote,
} from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { ClaimDetail as ClaimDetailType, Verdict } from "@/lib/types";
import { VERDICT_ORDER, flagLabel, verdictMeta } from "@/lib/utils";
import { Badge, Button, Card, ConfidenceMeter, EmptyState, SectionLabel, Spinner, VerdictBadge } from "@/components/ui";

const REDUNDANT_REASONS = new Set(["needs_human_review", "low_confidence"]);

function reviewSummaries(reasons: string[]): string {
  const useful = reasons.filter(
    (reason) => !REDUNDANT_REASONS.has(reason) && !reason.startsWith("verdict_"),
  );
  if (!useful.length) return "automated uncertainty — check the passage yourself";
  return useful.slice(0, 3).map(flagLabel).join(" · ");
}

const BASIS_LABEL: Record<string, string> = {
  full_text: "Full-text evidence",
  abstract_only: "Abstract only",
  none: "No evidence",
};

export function ClaimDetail() {
  const { id = "", claimId = "" } = useParams();
  const [detail, setDetail] = useState<ClaimDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [override, setOverride] = useState<Verdict | "">("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api
      .claim(claimId)
      .then((data) => {
        setDetail(data);
        setNote(data.verification?.reviewer_note ?? "");
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [claimId]);

  async function submitReview(action: "confirmed" | "overridden" | "note") {
    if (!detail) return;
    setSaving(true);
    setError("");
    setSaved("");
    try {
      const verification = await api.review(claimId, {
        action,
        new_verdict: action === "overridden" && override ? (override as Verdict) : undefined,
        note: note.trim() || undefined,
      });
      setDetail({ ...detail, verification });
      setSaved(action === "confirmed" ? "Verdict confirmed." : action === "overridden" ? "Verdict overridden." : "Note saved.");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-16 text-sm text-slate">
        <Spinner /> Loading claim…
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-16">
        <EmptyState
          title="Claim not found"
          description={error || "This claim could not be loaded."}
          action={
            <Link to={`/documents/${id}`}>
              <Button size="sm">Back to report</Button>
            </Link>
          }
        />
      </div>
    );
  }

  const verification = detail.verification;
  const primary = detail.references.find((link) => link.match_status === "matched") ?? detail.references[0];
  const reference = primary?.reference;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={`/documents/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate hover:text-ink"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to report
        </Link>
        <div className="flex items-center gap-2">
          {verification ? <VerdictBadge verdict={verification.verdict} /> : null}
          <Link
            to={`/documents/${id}/references`}
            className="text-xs font-medium text-slate hover:text-ink"
          >
            References
          </Link>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_300px]">
        <div className="space-y-4">
          <Card className="bg-lavender-soft p-5">
            <div className="flex items-center justify-between">
              <SectionLabel>Statement as written</SectionLabel>
              <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">
                page {detail.page_number ?? "—"}
              </span>
            </div>
            <p className="mt-3 text-[17px] font-semibold leading-relaxed text-ink sm:text-lg">
              “{detail.claim_text}”
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-1.5">
              {detail.section ? <Badge>{detail.section}</Badge> : null}
              <Badge>{detail.claim_category}</Badge>
              {detail.citation_markers.length ? (
                <Badge className="bg-white text-violet">{detail.citation_markers.join(" ")}</Badge>
              ) : (
                <Badge className="bg-orange-50 text-orange-800">no citation</Badge>
              )}
            </div>
          </Card>

          <Card className="overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
              <SectionLabel>Automated verdict</SectionLabel>
              <span className="text-[11px] text-slate">
                {BASIS_LABEL[verification?.evidence_basis ?? "none"] ?? verification?.evidence_basis} ·{" "}
                {verification?.reviewed_status ?? "pending"}
              </span>
            </div>
            <div className="p-5">
              {verification ? (
                <>
                  <div className="flex flex-wrap items-center gap-3">
                    <VerdictBadge verdict={verification.verdict} size="lg" />
                    <ConfidenceMeter level={verification.confidence_level} />
                  </div>
                  <p className="mt-3 text-[13.5px] leading-relaxed text-ink/85">{verification.explanation}</p>
                  {verification.confidence_reason ? (
                    <p className="mt-2 text-[11.5px] leading-relaxed text-slate">
                      Confidence: {verification.confidence_reason}
                    </p>
                  ) : null}

                  {verification.key_supporting_facts.length || verification.limitations.length ? (
                    <details className="mt-4 rounded-lg bg-paper/70 p-3">
                      <summary className="cursor-pointer text-[11.5px] font-medium text-slate">
                        Supporting facts and limitations
                      </summary>
                      <div className="mt-3 grid gap-4 sm:grid-cols-2">
                        <div>
                          <p className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">Supports</p>
                          <ul className="mt-1.5 space-y-1.5">
                            {verification.key_supporting_facts.map((fact) => (
                              <li key={fact} className="flex gap-2 text-[12px] leading-relaxed text-ink/75">
                                <Check className="mt-0.5 h-3 w-3 shrink-0 text-emerald-600" /> {fact}
                              </li>
                            ))}
                            {verification.key_supporting_facts.length === 0 ? (
                              <li className="text-[12px] text-slate">None recorded.</li>
                            ) : null}
                          </ul>
                        </div>
                        <div>
                          <p className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">Limits</p>
                          <ul className="mt-1.5 space-y-1.5">
                            {verification.limitations.map((item) => (
                              <li key={item} className="flex gap-2 text-[12px] leading-relaxed text-ink/75">
                                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" /> {item}
                              </li>
                            ))}
                            {verification.limitations.length === 0 ? (
                              <li className="text-[12px] text-slate">None recorded.</li>
                            ) : null}
                          </ul>
                        </div>
                      </div>
                    </details>
                  ) : null}

                  {verification.needs_human_review ? (
                    <div className="mt-3 flex flex-wrap items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-2 text-[11.5px] text-amber-800 ring-1 ring-amber-200">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Needs human review
                      <span className="text-amber-700/80">
                        {reviewSummaries(verification.review_reasons)}
                      </span>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="text-sm text-slate">No verification result yet.</p>
              )}
            </div>
          </Card>

          <div>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-base uppercase">Evidence from the source</h2>
              <span className="text-[11px] text-slate">{detail.evidence.length} passages</span>
            </div>
            {detail.evidence.length === 0 ? (
              <div className="mt-2 flex items-start gap-2 rounded-xl border border-dashed border-line bg-white/70 p-4 text-[12.5px] text-slate">
                <FileWarning className="mt-0.5 h-4 w-4 shrink-0" />
                No passage was retrieved, so this claim is marked for review instead of claiming support or refutation.
              </div>
            ) : (
              <div className="mt-2 space-y-2">
                {detail.evidence.map((evidence, index) => (
                  <Card key={evidence.id} className="p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">
                        <Quote className="h-3 w-3" />
                        {String(index + 1).padStart(2, "0")}
                        {evidence.source_section ? ` · ${evidence.source_section}` : ""}
                        {evidence.source_page ? ` · p.${evidence.source_page}` : ""}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {evidence.is_abstract_only ? (
                          <Badge className="bg-amber-50 text-amber-800">abstract only</Badge>
                        ) : null}
                        {evidence.quote_verified ? (
                          <Badge className="bg-emerald-50 text-emerald-800">
                            <BadgeCheck className="h-3 w-3" /> verbatim
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                    <p className="mt-2 border-l-2 border-violet/30 pl-3 text-[13px] leading-relaxed text-ink/85">
                      {evidence.passage}
                    </p>
                    {evidence.source_url ? (
                      <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-violet hover:underline"
                      >
                        Open at source <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : null}
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-4">
          <Card className="p-4">
            <SectionLabel>Cited paper</SectionLabel>
            {reference ? (
              <div className="mt-2 space-y-1.5">
                <p className="text-[13px] font-semibold leading-snug">
                  {reference.matched_title ?? reference.title ?? "Title unavailable"}
                </p>
                <p className="text-[11.5px] leading-relaxed text-slate">
                  {reference.matched_authors.slice(0, 3).join(", ") || reference.authors.slice(0, 3).join(", ") || "Authors unavailable"}
                  {reference.matched_year ?? reference.year ? ` · ${reference.matched_year ?? reference.year}` : ""}
                </p>
                {reference.publication_source ? (
                  <p className="text-[11.5px] italic text-slate">{reference.publication_source}</p>
                ) : null}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <Badge className="bg-paper">{reference.matching_status}</Badge>
                  <Badge className="bg-paper">{reference.fulltext_availability.replaceAll("_", " ")}</Badge>
                </div>
                {reference.matched_source_url ? (
                  <a
                    href={reference.matched_source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 flex items-center justify-between rounded-lg bg-paper px-2.5 py-2 text-[11.5px] font-medium text-ink hover:bg-lavender-soft"
                  >
                    {reference.matched_doi ? `doi:${reference.matched_doi}` : "Open source"}
                    <ArrowUpRight className="h-3.5 w-3.5 text-violet" />
                  </a>
                ) : (
                  <p className="mt-1 rounded-lg border border-dashed border-line px-2.5 py-2 text-[11px] text-slate">
                    No public source link confirmed.
                  </p>
                )}
                {reference.flags.length ? (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {reference.flags.slice(0, 4).map((flag) => (
                      <Badge key={flag} className="bg-orange-50 text-orange-800">
                        {flagLabel(flag)}
                      </Badge>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="mt-2 text-[12px] leading-relaxed text-slate">
                No reference matched this claim, so there is no paper to inspect.
              </p>
            )}
          </Card>

          <Card className="p-4">
            <SectionLabel className="flex items-center gap-1.5">
              <ClipboardCheck className="h-3.5 w-3.5" /> Review
            </SectionLabel>
            <div className="mt-2 space-y-2">
              <select
                value={override}
                onChange={(event) => setOverride(event.target.value as Verdict | "")}
                className="h-9 w-full rounded-lg border border-line bg-white px-2 text-xs outline-none focus:border-violet"
                aria-label="Override verdict"
              >
                <option value="">Keep current verdict</option>
                {VERDICT_ORDER.map((verdict) => (
                  <option key={verdict} value={verdict}>
                    {verdictMeta(verdict).label}
                  </option>
                ))}
              </select>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={2}
                placeholder="Reviewer note (optional)"
                className="w-full rounded-lg border border-line bg-white p-2 text-xs outline-none focus:border-violet"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={() => submitReview("confirmed")} disabled={saving} className="flex-1">
                  Confirm
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => submitReview("overridden")}
                  disabled={saving || !override}
                >
                  Override
                </Button>
              </div>
              <button
                type="button"
                onClick={() => submitReview("note")}
                disabled={saving || !note.trim()}
                className="w-full text-[11px] text-slate hover:text-ink disabled:opacity-40"
              >
                Save note only
              </button>
              {saved ? <p className="rounded-md bg-emerald-50 px-2 py-1 text-[11px] text-emerald-800">{saved}</p> : null}
              {error ? <p className="rounded-md bg-red-50 px-2 py-1 text-[11px] text-danger">{error}</p> : null}
            </div>
          </Card>

          <p className="px-1 text-[10.5px] leading-relaxed text-slate">
            Confidence reflects evidence strength, not a probability that the claim is true.
          </p>
        </aside>
      </div>
    </div>
  );
}
