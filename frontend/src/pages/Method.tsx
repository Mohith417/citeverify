import { Link } from "react-router-dom";
import { ArrowUpRight, FileText, ScanSearch, ShieldCheck } from "lucide-react";
import { Button, SectionLabel, VerdictBadge } from "@/components/ui";
import { PageHeading } from "@/components/Layout";
import { VERDICT_ORDER } from "@/lib/utils";

const STEPS = [
  {
    icon: FileText,
    title: "Read",
    body: "Text and page numbers come from pypdf. Claims, citation markers and the bibliography are parsed.",
    tone: "bg-lavender",
  },
  {
    icon: ScanSearch,
    title: "Trace",
    body: "Each reference is resolved by DOI, then exact title, and its open-access full text is fetched where legal.",
    tone: "bg-coral-soft",
  },
  {
    icon: ShieldCheck,
    title: "Compare",
    body: "Relevant paragraphs are compared with the claim. Quotations are checked against the source text.",
    tone: "bg-mint",
  },
];

export function Method() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-10 sm:px-6">
      <PageHeading
        eyebrow="Method"
        title="How a verdict happens"
        description="We find the paper that was cited, read it, and show what it actually says."
        actions={
          <Link to="/upload">
            <Button size="sm">
              Try it <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        }
      />

      <div className="mt-6 space-y-3">
        {STEPS.map(({ icon: Icon, title, body, tone }, index) => (
          <div
            key={title}
            className="group flex gap-4 border-2 border-ink bg-white p-5 transition-all duration-150 hover:-translate-x-[2px] hover:-translate-y-[2px] hover:shadow-block-sm"
          >
            <span className={`flex h-11 w-11 shrink-0 items-center justify-center border-2 border-ink ${tone} transition-transform duration-200 group-hover:-rotate-6`}>
              <Icon className="h-4 w-4" />
            </span>
            <div>
              <p className="font-display text-base uppercase">
                <span className="mr-2 font-mono text-[11px] text-slate">{String(index + 1).padStart(2, "0")}</span>
                {title}
              </p>
              <p className="mt-1 text-[12.5px] leading-relaxed text-slate">{body}</p>
            </div>
          </div>
        ))}
      </div>

      <section className="mt-10">
        <SectionLabel>Verdicts</SectionLabel>
        <h2 className="display mt-1.5 text-2xl">What each answer means</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {VERDICT_ORDER.map((verdict) => (
            <span key={verdict} className="transition-transform duration-150 hover:-translate-y-1">
              <VerdictBadge verdict={verdict} />
            </span>
          ))}
        </div>
        <p className="mt-5 border-l-4 border-coral bg-white px-4 py-3 text-[12px] leading-relaxed text-slate">
          “Unsupported” never means “false” — only that the accessible evidence didn't establish the statement.
          Only public sources are fetched, and every non-supported result is marked for human review.
        </p>
      </section>
    </div>
  );
}
