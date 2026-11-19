import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, ArrowUpRight, CheckCircle2, ChevronDown, FileText, HelpCircle } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import type { DocumentResults, Reference } from "@/lib/types";
import { flagLabel } from "@/lib/utils";
import { Badge, Button, Card, EmptyState, SectionLabel, Spinner } from "@/components/ui";

const STATUS: Record<string, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  matched: { label: "Matched", className: "bg-emerald-50 text-emerald-800", icon: CheckCircle2 },
  ambiguous: { label: "Ambiguous", className: "bg-amber-50 text-amber-800", icon: HelpCircle },
  not_found: { label: "Not found", className: "bg-orange-50 text-orange-800", icon: AlertTriangle },
  incomplete: { label: "Incomplete", className: "bg-paper text-slate", icon: FileText },
  pending: { label: "Pending", className: "bg-paper text-slate", icon: FileText },
};

export function References() {
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
        <Spinner /> Loading references…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-16">
        <EmptyState title="References unavailable" description={error || "This document could not be loaded."} />
      </div>
    );
  }

  const references = data.references;
  const matched = references.filter((ref) => ref.matching_status === "matched").length;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6">
      <Link to={`/documents/${id}`} className="inline-flex items-center gap-1.5 text-xs font-medium text-slate hover:text-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to report
      </Link>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="display text-2xl sm:text-3xl">References</h1>
          <p className="mt-1 text-xs text-slate">
            {matched} of {references.length} entries resolved to an original publication
          </p>
        </div>
        <a href={api.reportUrl(id)} target="_blank" rel="noreferrer">
          <Button size="sm" variant="dark">
            Download report
          </Button>
        </a>
      </div>

      {references.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="No reference list detected"
            description="No References or Bibliography heading was found in this PDF, so citations could not be mapped."
          />
        </div>
      ) : (
        <div className="mt-6 space-y-2">
          {references.map((reference) => (
            <ReferenceRow key={reference.id} reference={reference} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReferenceRow({ reference }: { reference: Reference }) {
  const meta = STATUS[reference.matching_status] ?? STATUS.pending;
  const Icon = meta.icon;
  const title = reference.matched_title ?? reference.title ?? reference.reference_text;
  return (
    <details className="group border-2 border-ink bg-white transition-shadow hover:shadow-block-sm open:shadow-block-sm">
      <summary className="flex cursor-pointer list-none items-start gap-3 p-4 [&::-webkit-details-marker]:hidden">
        <span className="flex h-7 min-w-7 shrink-0 items-center justify-center rounded-md bg-lavender-soft px-1 font-mono text-[10.5px]">
          {reference.ref_label || "—"}
        </span>
        <div className="min-w-0 flex-1">
          <p className="line-clamp-1 text-[13px] font-medium text-ink">{title}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge className={meta.className}>
              <Icon className="h-3 w-3" /> {meta.label}
            </Badge>
            {reference.matched_year ?? reference.year ? <Badge>{reference.matched_year ?? reference.year}</Badge> : null}
            <Badge>{reference.fulltext_availability.replaceAll("_", " ")}</Badge>
          </div>
        </div>
        <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-slate transition-transform group-open:rotate-180" />
      </summary>

      <div className="space-y-4 border-t-2 border-ink/10 p-4">
        <p className="break-words text-[12px] leading-relaxed text-slate">{reference.reference_text}</p>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="min-w-0">
            <SectionLabel>Matched publication</SectionLabel>
            {reference.matched_title ? (
              <div className="mt-1.5 space-y-1">
                <p className="text-[12.5px] font-semibold leading-snug">{reference.matched_title}</p>
                <p className="text-[11.5px] text-slate">
                  {reference.matched_authors.slice(0, 4).join(", ") || "authors unavailable"}
                  {reference.matched_year ? ` · ${reference.matched_year}` : ""}
                </p>
                {reference.publication_source ? (
                  <p className="text-[11.5px] italic text-slate">{reference.publication_source}</p>
                ) : null}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  {reference.matched_doi ? (
                    <a
                      href={`https://doi.org/${reference.matched_doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded-md bg-paper px-2 py-1 font-mono text-[10px] text-violet hover:bg-lavender-soft"
                    >
                      doi:{reference.matched_doi} <ArrowUpRight className="h-3 w-3" />
                    </a>
                  ) : null}
                  {reference.matched_source_url ? (
                    <a
                      href={reference.matched_source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-medium text-violet hover:underline"
                    >
                      source <ArrowUpRight className="h-3 w-3" />
                    </a>
                  ) : null}
                </div>
              </div>
            ) : (
              <p className="mt-1.5 text-[12px] leading-relaxed text-slate">
                No publication confirmed — kept for human review rather than guessed.
              </p>
            )}
          </div>

          <div className="min-w-0">
            <SectionLabel>Parsed metadata</SectionLabel>
            <dl className="mt-1.5 space-y-1 text-[11.5px]">
              {[
                ["Title", reference.title ?? "—"],
                ["Year", reference.year?.toString() ?? "—"],
                ["DOI", reference.doi ?? "—"],
                ["Authors", reference.authors.slice(0, 3).join(", ") || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate">{label}</dt>
                  <dd className="truncate text-right">{value}</dd>
                </div>
              ))}
            </dl>
            {reference.flags.length ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {reference.flags.map((flag) => (
                  <Badge key={flag} className="bg-orange-50 text-orange-800">
                    {flagLabel(flag)}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        {reference.abstract ? (
          <details className="rounded-lg bg-paper/70 p-3">
            <summary className="cursor-pointer text-[11px] font-medium text-slate">Abstract retrieved</summary>
            <p className="mt-2 max-h-40 overflow-y-auto text-[11.5px] leading-relaxed text-ink/70">
              {reference.abstract}
            </p>
          </details>
        ) : null}

        {reference.candidates?.length ? (
          <details className="rounded-lg bg-paper/70 p-3">
            <summary className="cursor-pointer text-[11px] font-medium text-slate">
              Candidate papers considered ({reference.candidates.length})
            </summary>
            <ul className="mt-2 space-y-1">
              {reference.candidates.map((candidate, index) => {
                const record = candidate as Record<string, unknown>;
                const doi = record.doi ? String(record.doi) : "";
                return (
                  <li key={`${record.title}-${index}`} className="flex items-center justify-between gap-2 text-[11.5px]">
                    <span className="truncate">
                      {String(record.title ?? "Untitled")}
                      {record.year ? ` · ${record.year}` : ""}
                    </span>
                    {doi ? (
                      <a href={`https://doi.org/${doi}`} target="_blank" rel="noreferrer" className="font-mono text-[10px] text-violet hover:underline">
                        {doi}
                      </a>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </details>
        ) : null}
      </div>
    </details>
  );
}
