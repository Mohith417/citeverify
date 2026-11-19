import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, FileUp, Quote, ScanSearch, ShieldCheck } from "lucide-react";
import { Button, VerdictBadge } from "@/components/ui";
import { VERDICT_META, VERDICT_ORDER } from "@/lib/utils";

const STEPS = [
  {
    icon: FileUp,
    n: "01",
    title: "Drop a paper",
    line: "Claims, citation markers and the bibliography are pulled out, page by page.",
    tone: "#DCD3E3",
  },
  {
    icon: ScanSearch,
    n: "02",
    title: "We trace the source",
    line: "Each reference is matched to the real publication and its open-access text.",
    tone: "#F0DCD0",
  },
  {
    icon: ShieldCheck,
    n: "03",
    title: "You see the evidence",
    line: "A verdict, a confidence level and the exact passage behind it.",
    tone: "#CBD7C6",
  },
];

const STATS = [
  { value: "8", label: "research APIs" },
  { value: "6", label: "verdicts" },
  { value: "100%", label: "reviewable" },
];

export function Landing() {
  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden border-b-2 border-ink">
        <div className="absolute inset-0 grid-lines opacity-50" aria-hidden />
        <div
          className="absolute -right-20 top-10 h-56 w-56 rounded-full bg-lavender/50 blur-2xl"
          aria-hidden
        />
        <div
          className="absolute -left-16 bottom-0 h-40 w-40 rounded-full bg-coral-soft/60 blur-2xl"
          aria-hidden
        />

        <div className="relative mx-auto grid w-full max-w-6xl items-center gap-10 px-4 pb-14 pt-10 sm:px-6 lg:grid-cols-[1.02fr_0.98fr] lg:gap-8 lg:pb-16 lg:pt-12">
          <div className="animate-rise">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 bg-coral ring-2 ring-ink" />
              <span className="label-mono text-ink/70">Scientific claim verification</span>
            </div>

            <h1 className="display mt-5 text-[38px] leading-[0.92] sm:text-[48px] lg:text-[50px] xl:text-[60px]">
              Citations
              <br />
              aren't&nbsp;
              <span className="relative inline-block bg-violet px-2 text-paper">
                proof
                <span className="absolute -bottom-2 -right-2 -z-10 h-full w-full border-2 border-ink bg-coral transition-transform duration-300 ease-smooth group-hover:translate-x-1" />
              </span>
              <span className="text-coral">.</span>
            </h1>

            <p className="mt-6 max-w-md text-[14px] leading-relaxed text-ink/70">
              CiteVerify finds the paper behind each citation, reads it, and tells you whether it
              really supports the claim.
            </p>

              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Link to="/upload" className="arrow-slide">
                  <Button size="lg">
                    Verify a document <ArrowUpRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link to="/method">
                  <Button size="lg" variant="outline">
                    How it works <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>

            <dl className="mt-8 flex flex-wrap items-center gap-x-7 gap-y-3">
              {STATS.map((stat) => (
                <div key={stat.label} className="group flex items-baseline gap-2">
                  <dt className="font-display text-xl leading-none transition-transform duration-300 ease-smooth group-hover:-translate-y-[1px] group-hover:text-violet">
                    {stat.value}
                  </dt>
                  <dd className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
                    {stat.label}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* collage: claim + the passage that decides it */}
          <div className="relative mx-auto h-[420px] w-full max-w-[440px] animate-rise sm:h-[440px] [animation-delay:120ms]">
            <div
              className="absolute inset-y-8 left-10 right-6 rotate-[-4deg] border-2 border-ink bg-lavender"
              aria-hidden
            />

            <div className="group absolute right-0 top-0 w-[86%] rotate-[2deg] border-2 border-ink bg-white p-5 shadow-block transition-all duration-300 ease-smooth hover:-translate-y-1 hover:rotate-0 hover:shadow-block-sm">
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                <span>Claim 04</span>
                <span className="border border-ink/20 px-1.5 py-0.5">p. 3</span>
              </div>
              <p className="mt-3 text-[15px] font-semibold leading-snug">
                “A randomized trial found the app improved test scores by 30%.”
              </p>
              <div className="mt-4 flex items-center justify-between">
                <VerdictBadge verdict="partially_supported" size="sm" />
                <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">
                  confidence · med
                </span>
              </div>
              <p className="mt-3 border-t-2 border-line pt-3 text-[11.5px] leading-relaxed text-slate">
                The paper reports improvement in a small pilot, but no 30% increase.
              </p>
            </div>

            <div className="group absolute bottom-0 left-0 w-[78%] rotate-[-2deg] border-2 border-ink bg-violet p-5 text-paper shadow-block transition-all duration-300 ease-smooth hover:-translate-y-1 hover:rotate-0">
              <Quote className="h-5 w-5 text-paper/70 transition-transform duration-300 group-hover:-translate-y-0.5" />
              <p className="mt-2 text-[13px] font-medium leading-snug">
                “Participants in the intervention arm improved, although the study was a small
                pilot.”
              </p>
              <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.14em] text-paper/60">
                verbatim · results section
              </p>
            </div>

            <img
              src="/logo.png"
              alt=""
              className="absolute -bottom-3 right-2 h-14 w-14 rotate-6 border-2 border-ink object-cover shadow-block-sm transition-all duration-300 ease-smooth hover:-rotate-6 hover:scale-105"
            />
            <span className="absolute left-8 top-10 h-6 w-6 rotate-12 border-2 border-ink bg-coral" aria-hidden />
            <span className="absolute right-10 bottom-28 h-3 w-3 rounded-full bg-ink" aria-hidden />
          </div>
        </div>
      </section>

      {/* STEPS */}
      <section className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3 pb-4">
          <h2 className="display text-2xl sm:text-3xl">How a check runs</h2>
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate">
            Three steps · nothing invented
          </span>
        </div>

        <div className="border-y-2 border-ink">
          {STEPS.map(({ icon: Icon, ...step }) => (
            <Link
              key={step.n}
              to="/method"
              className="row-fill group flex flex-col gap-2 px-3 py-6 sm:flex-row sm:items-center sm:gap-7 sm:px-5"
              style={{ "--row-fill": step.tone } as React.CSSProperties}
            >
              <span className="flex items-center gap-3">
                <span
                  className="flex h-9 w-9 shrink-0 items-center justify-center border-2 border-ink bg-white transition-transform duration-300 ease-smooth group-hover:-rotate-6 group-hover:scale-105"
                  style={{ backgroundColor: step.tone }}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span className="font-mono text-[11px] tracking-[0.18em] text-slate transition-colors duration-300 group-hover:text-ink">
                  {step.n}
                </span>
              </span>
              <h3 className="display text-2xl transition-transform duration-500 ease-smooth group-hover:translate-x-1.5 sm:w-[46%] sm:text-[30px]">
                {step.title}
              </h3>
              <p className="text-[13px] leading-relaxed text-ink/65 sm:flex-1">{step.line}</p>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center border-2 border-ink bg-white transition-all duration-300 ease-smooth group-hover:-rotate-45 group-hover:border-ink group-hover:bg-ink group-hover:text-paper">
                <ArrowUpRight className="h-4 w-4" />
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* VERDICTS */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-12 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3 pb-4">
          <h2 className="display text-2xl sm:text-3xl">Six honest verdicts</h2>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate">
            “unsupported” ≠ “false”
          </p>
        </div>

        <div className="grid gap-[2px] border-2 border-ink bg-ink sm:grid-cols-2 lg:grid-cols-3">
          {VERDICT_ORDER.map((verdict, index) => {
            const meta = VERDICT_META[verdict];
            return (
              <div
                key={verdict}
                className="group relative bg-paper p-5 transition-colors duration-200 hover:bg-white"
              >
                <span className="absolute right-4 top-4 font-mono text-[10px] text-ink/25 transition-all duration-300 ease-smooth group-hover:-translate-y-0.5 group-hover:text-violet/60">
                  0{index + 1}
                </span>
                <VerdictBadge verdict={verdict} />
                <p className="mt-3 max-w-[26ch] text-[12px] leading-relaxed text-ink/60 transition-colors duration-200 group-hover:text-ink/80">
                  {meta.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-6 sm:px-6">
        <div className="group relative overflow-hidden border-2 border-ink bg-ink px-6 py-10 text-paper transition-colors duration-300 hover:bg-[#2a2720] sm:px-10">
          <div
            className="stripes pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute -right-10 -top-12 h-44 w-44 rounded-full border-2 border-lavender/20 bg-violet/30 blur-[1px] transition-transform duration-700 ease-smooth group-hover:-translate-x-4 group-hover:translate-y-3"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute bottom-6 right-24 h-9 w-9 rotate-12 bg-coral transition-transform duration-500 ease-smooth group-hover:rotate-[64deg]"
            aria-hidden
          />
          <div className="relative flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <h2 className="display text-2xl sm:text-4xl">
                Check the evidence.
                <br />
                <span className="text-lavender">Not just the reference.</span>
              </h2>
              <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.16em] text-paper/45">
                Free research APIs · no paywall bypassing
              </p>
            </div>
            <Link to="/upload" className="arrow-slide">
              <Button size="lg" variant="coral">
                Start verifying <ArrowUpRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
