import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  CircleCheck,
  FileSearch,
  Link2,
  Quote,
  ScanSearch,
  ShieldAlert,
  Waypoints,
} from "lucide-react";
import { Button, Card, SectionLabel, VerdictBadge } from "@/components/ui";
import { VERDICT_META, VERDICT_ORDER } from "@/lib/utils";

const STEPS = [
  { n: "01", title: "Upload", body: "A paper, assignment or report as a text-based PDF." },
  { n: "02", title: "Extract", body: "Claims, in-text citations and the bibliography are parsed." },
  { n: "03", title: "Retrieve", body: "The cited publication is located and legal open text fetched." },
  { n: "04", title: "Compare", body: "Claim wording, numbers and scope are checked against the source." },
  { n: "05", title: "Report", body: "Verdicts, quotations, confidence and review flags in one report." },
];

const NEVER = [
  "Invent a paper, DOI or quotation — every quote is matched against retrieved text.",
  "Present an abstract as if the whole study was read.",
  "Call a paper outdated just because it is old.",
  "Accept a similar title as the cited paper without matching metadata.",
  "Treat an automated verdict as a final academic judgment.",
];

export function Landing() {
  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden border-b-2 border-ink bg-lavender">
        <div className="absolute inset-0 grid-lines opacity-70" aria-hidden />
        <div className="absolute -left-10 top-24 h-28 w-28 rounded-full bg-coral" aria-hidden />
        <div className="absolute bottom-10 left-1/3 h-16 w-16 rotate-12 border-2 border-ink bg-white" aria-hidden />
        <div className="absolute -right-8 top-10 h-24 w-24 border-2 border-ink bg-violet" aria-hidden />
        <div className="relative mx-auto grid w-full max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <div className="animate-rise">
            <SectionLabel className="flex items-center gap-2 text-ink/70">
              <span className="h-2 w-2 bg-coral" />
              Research technology · academic integrity
            </SectionLabel>
            <h1 className="display mt-5 text-[13vw] leading-[0.88] sm:text-6xl lg:text-7xl">
              A citation
              <br />
              is not
              <br />
              <span className="relative inline-block">
                <span className="absolute inset-x-0 bottom-1 h-4 bg-coral/70" aria-hidden />
                <span className="relative">proof.</span>
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-ink/75 sm:text-lg">
              CiteVerify reads a document, finds the claims that need evidence, tracks down the
              original research and checks whether that research <em className="not-italic font-semibold">actually supports</em>{" "}
              what was written — with the source passage attached.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to="/upload">
                <Button size="lg" variant="primary">
                  Upload a document
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/method">
                <Button size="lg" variant="outline">
                  How verification works
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 font-mono text-[10px] uppercase tracking-[0.14em] text-ink/60">
              <span>Real PDF parsing</span>
              <span>DOI &amp; title matching</span>
              <span>Open-access full text</span>
              <span>Human review flags</span>
            </div>
          </div>

          {/* collage */}
          <div className="relative mx-auto h-[430px] w-full max-w-lg animate-rise [animation-delay:120ms]">
            <div className="absolute right-0 top-4 w-[74%] rotate-[6deg] border-2 border-ink bg-white p-4 shadow-block">
              <div className="flex items-center justify-between border-b border-line pb-2">
                <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-slate">claim 04 / evidence</span>
                <span className="h-2 w-2 bg-violet" />
              </div>
              <p className="mt-3 text-[13px] font-medium leading-snug">
                “A randomized trial found the app improved test scores by 30%.”
              </p>
              <div className="mt-3 flex items-center justify-between">
                <VerdictBadge verdict="partially_supported" size="sm" />
                <span className="font-mono text-[9px] text-slate">confidence · medium</span>
              </div>
              <div className="mt-3 border-t border-line pt-2 text-[10.5px] leading-relaxed text-slate">
                Source reports improvement in a small pilot group; no 30% figure appears in the results.
              </div>
            </div>

            <div className="absolute -left-2 top-0 w-[62%] -rotate-[6deg] border-2 border-ink bg-violet p-5 text-white shadow-block">
              <ScanSearch className="h-7 w-7" />
              <p className="mt-6 font-display text-2xl uppercase leading-none">
                Does the
                <br /> source agree?
              </p>
              <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.16em] text-white/70">
                6 verdict states · 1 trace
              </p>
            </div>

            <div className="absolute bottom-6 left-2 w-[68%] rotate-[-2deg] border-2 border-ink bg-coral p-4 text-white shadow-block">
              <Quote className="h-5 w-5" />
              <p className="mt-3 text-[12px] font-medium leading-snug">
                “Participants in the intervention arm improved, but the study was a small pilot.”
              </p>
              <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.14em] text-white/80">
                verbatim passage · results
              </p>
            </div>

            <div className="absolute bottom-0 right-2 flex w-[44%] flex-col gap-2 border-2 border-ink bg-white p-3 shadow-block-sm">
              <div className="flex items-center justify-between">
                <Link2 className="h-4 w-4" />
                <span className="font-mono text-[9px] text-slate">DOI</span>
              </div>
              <p className="text-[11px] font-semibold leading-tight">Original publication matched</p>
              <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-emerald-700">open access · full text</p>
            </div>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className="border-b-2 border-ink bg-ink text-white">
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-14 sm:px-6 md:grid-cols-[0.9fr_1.1fr]">
          <div>
            <SectionLabel className="text-white/50">The problem</SectionLabel>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Genuine paper.
              <br />
              Wrong claim.
            </h2>
          </div>
          <div className="grid gap-5 sm:grid-cols-3">
            {[
              { icon: FileSearch, title: "Slow to check", body: "Verifying every reference by hand does not fit a submission deadline." },
              { icon: ShielAlertIcon, title: "Misread findings", body: "A real study can be cited for a conclusion it never tested." },
              { icon: Waypoints, title: "Numbers drift", body: "Percentages and sample sizes get exaggerated between drafts." },
            ].map(({ icon: Icon, title, body }) => (
              <div key={title} className="border border-white/15 p-4">
                <Icon className="h-5 w-5 text-lavender" />
                <p className="mt-4 text-sm font-semibold">{title}</p>
                <p className="mt-1.5 text-[12.5px] leading-relaxed text-white/65">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WORKFLOW */}
      <section className="border-b-2 border-ink bg-paper">
        <div className="mx-auto w-full max-w-7xl px-4 py-16 sm:px-6">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <SectionLabel>The workflow</SectionLabel>
              <h2 className="display mt-3 text-3xl sm:text-4xl">Five stages, no shortcuts</h2>
            </div>
            <p className="max-w-md text-sm leading-relaxed text-slate">
              Each stage reports what it actually did. If a source cannot be retrieved or matched,
              the claim is flagged for review instead of being given a fabricated verdict.
            </p>
          </div>
          <div className="mt-10 grid gap-0 border-2 border-ink md:grid-cols-5">
            {STEPS.map((step, index) => (
              <div
                key={step.n}
                className={[
                  "group relative flex flex-col gap-3 border-ink p-5 transition-colors",
                  index !== STEPS.length - 1 ? "border-b-2 md:border-b-0 md:border-r-2" : "",
                  index % 2 === 0 ? "bg-white" : "bg-lavender-soft",
                  "hover:bg-violet hover:text-white",
                ].join(" ")}
              >
                <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-slate group-hover:text-white/70">
                  {step.n}
                </span>
                <span className="font-display text-xl uppercase">{step.title}</span>
                <span className="text-[12.5px] leading-relaxed text-slate group-hover:text-white/80">{step.body}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VERDICTS */}
      <section className="border-b-2 border-ink bg-lavender-soft">
        <div className="mx-auto w-full max-w-7xl px-4 py-16 sm:px-6">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <SectionLabel>Claim status classification</SectionLabel>
              <h2 className="display mt-3 text-3xl sm:text-4xl">Six honest verdicts</h2>
            </div>
            <p className="max-w-md text-sm leading-relaxed text-slate">
              “Unsupported” means the evidence did not establish the claim — never that the claim was
              disproven. Uncertainty is a first-class outcome.
            </p>
          </div>
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {VERDICT_ORDER.map((verdict) => (
              <Card key={verdict} className="flex flex-col gap-3 p-5">
                <VerdictBadge verdict={verdict} />
                <p className="text-[12.5px] leading-relaxed text-slate">{VERDICT_META[verdict].description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* GUARDRAILS */}
      <section className="border-b-2 border-ink bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <SectionLabel>Guardrails</SectionLabel>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Built to say
              <br />
              “I don't know”
            </h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-slate">
              A verification tool is only useful if it refuses to bluff. CiteVerify keeps the original
              document untouched, shows the retrieved passage, and marks what a human should check.
            </p>
            <div className="mt-6 flex items-center gap-3 border-2 border-ink bg-mint p-4">
              <CircleCheck className="h-5 w-5" />
              <p className="text-[12.5px] font-medium leading-snug">
                Every finding includes a confidence level and is open to review, confirmation or override.
              </p>
            </div>
          </div>
          <div className="divide-y-2 divide-ink/10 border-2 border-ink">
            <div className="flex items-center gap-2 bg-coral/10 px-4 py-3">
              <ShieldAlert className="h-4 w-4 text-coral" />
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-ink/70">
                What CiteVerify never does
              </span>
            </div>
            {NEVER.map((item) => (
              <div key={item} className="flex gap-3 px-4 py-4">
                <span className="mt-1.5 h-2 w-2 shrink-0 bg-ink" />
                <p className="text-[13px] leading-relaxed text-ink/80">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SOURCES */}
      <section className="border-b-2 border-ink bg-paper">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-12 sm:px-6">
          <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
            <SectionLabel>Research infrastructure</SectionLabel>
            <p className="text-[11px] text-slate">Free and open APIs only · keys never reach the browser</p>
          </div>
          <div className="grid grid-cols-2 gap-px border-2 border-ink bg-ink sm:grid-cols-4 lg:grid-cols-7">
            {["Crossref", "OpenAlex", "Europe PMC", "Semantic Scholar", "Unpaywall", "arXiv", "GROBID"].map((name) => (
              <div key={name} className="flex h-20 items-center justify-center bg-white px-2 text-center font-display text-[13px] uppercase">
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-violet text-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-start justify-between gap-6 px-4 py-16 sm:px-6 md:flex-row md:items-center">
          <div>
            <h2 className="display text-3xl sm:text-4xl">
              Check the evidence,
              <br />
              not just the reference.
            </h2>
            <p className="mt-3 max-w-xl text-sm text-white/75">
              Upload a PDF and get a claim-by-claim verification report with source links.
            </p>
          </div>
          <Link to="/upload">
            <Button size="lg" variant="secondary">
              Start a verification
              <ArrowUpRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

function ShielAlertIcon(props: React.ComponentProps<typeof ShieldAlert>) {
  return <ShieldAlert {...props} />;
}
