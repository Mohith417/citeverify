import { Link } from "react-router-dom";
import { ArrowUpRight, Database, FileSearch, Gauge, Layers, Link2, ScanText, ShieldCheck } from "lucide-react";
import { Button, Card, SectionLabel, VerdictBadge } from "@/components/ui";
import { PageHeading } from "@/components/Layout";
import { VERDICT_META, VERDICT_ORDER } from "@/lib/utils";

const MODULES = [
  {
    icon: ScanText,
    title: "Document & claim extraction",
    body: "pypdf extracts text page by page (with scanned-PDF detection). The LLM identifies statements that need evidence and stores the exact original wording.",
  },
  {
    icon: Link2,
    title: "Citation detection & mapping",
    body: "Numeric markers ([1], [2,3], [1–4]) and author–year citations are parsed, matched to the bibliography and flagged when ambiguous.",
  },
  {
    icon: Database,
    title: "Original paper retrieval",
    body: "DOI lookup first, then exact title, then title + author/year across Crossref, OpenAlex, Europe PMC, Semantic Scholar and arXiv. Similar titles are not accepted silently.",
  },
  {
    icon: FileSearch,
    title: "Full-text evidence",
    body: "Open-access PDFs from OpenAlex/Unpaywall and Europe PMC XML are downloaded behind an SSRF guard. Abstracts are labelled as abstract-only.",
  },
  {
    icon: Layers,
    title: "Evidence comparison",
    body: "Section-aware paragraphs are ranked against the claim (sentence embeddings when available, lexical BM25 otherwise) and the best passages go to the verifier.",
  },
  {
    icon: Gauge,
    title: "Verdicts & confidence",
    body: "The model returns structured JSON: verdict, explanation, supporting facts, limitations, confidence and review flag. Quotations are checked against the source text.",
  },
];

export function Method() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Method & guardrails"
        title="How CiteVerify reaches a verdict"
        description="A citation is a pointer, not proof. The pipeline is designed around retrieving the cited research and showing the exact basis for every result."
        actions={
          <Link to="/upload">
            <Button size="sm">
              Try it <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        }
      />

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {MODULES.map(({ icon: Icon, title, body }, index) => (
          <Card key={title} className="flex gap-4 p-5">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-ink bg-lavender">
              <Icon className="h-4 w-4" />
            </span>
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">Module {String(index + 1).padStart(2, "0")}</p>
              <h2 className="mt-1 text-sm font-semibold">{title}</h2>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-slate">{body}</p>
            </div>
          </Card>
        ))}
      </div>

      <section className="mt-12">
        <SectionLabel>Verdict definitions</SectionLabel>
        <h2 className="display mt-2 text-2xl sm:text-3xl">What each status means</h2>
        <div className="mt-5 divide-y-2 divide-ink/10 border-2 border-ink bg-white">
          {VERDICT_ORDER.map((verdict) => (
            <div key={verdict} className="grid gap-2 px-4 py-4 sm:grid-cols-[200px_1fr] sm:items-center">
              <VerdictBadge verdict={verdict} />
              <p className="text-[13px] leading-relaxed text-ink/80">{VERDICT_META[verdict].description}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[12px] leading-relaxed text-slate">
          “Unsupported” is not the same as “false”: it means the accessible evidence did not establish the statement.
          Every non-supported verdict is automatically marked for human review.
        </p>
      </section>

      <section className="mt-12 grid gap-4 md:grid-cols-2">
        <Card className="bg-ink p-6 text-white">
          <ShieldCheck className="h-6 w-6 text-lavender" />
          <h2 className="mt-4 font-display text-xl uppercase">Reliability rules</h2>
          <ul className="mt-3 space-y-2 text-[12.5px] leading-relaxed text-white/75">
            <li>• Only publicly reachable http(s) sources are fetched; private addresses are refused.</li>
            <li>• Quotations must appear in the retrieved source text or they are removed.</li>
            <li>• No full text ⇒ the report says so and marks the claim for review.</li>
            <li>• Human review actions are stored with a reviewer note.</li>
          </ul>
        </Card>
        <Card className="p-6">
          <h2 className="font-display text-xl uppercase">Evidence basis</h2>
          <div className="mt-4 space-y-3 text-[12.5px] leading-relaxed">
            <div className="flex items-start gap-3 border border-line p-3">
              <span className="mt-1 h-2 w-2 shrink-0 bg-emerald-600" />
              <p><strong>Full text</strong> — the verdict is based on paragraphs from the paper itself.</p>
            </div>
            <div className="flex items-start gap-3 border border-line p-3">
              <span className="mt-1 h-2 w-2 shrink-0 bg-amber-500" />
              <p><strong>Abstract only</strong> — limited analysis, clearly labelled, never full-text confirmation.</p>
            </div>
            <div className="flex items-start gap-3 border border-line p-3">
              <span className="mt-1 h-2 w-2 shrink-0 bg-slate-400" />
              <p><strong>No evidence</strong> — the claim is marked insufficient evidence and sent to review.</p>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
