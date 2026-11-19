import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, FileUp, Quote, ScanSearch, ShieldCheck } from "lucide-react";
import { Button, VerdictBadge } from "@/components/ui";
import { VERDICT_ORDER } from "@/lib/utils";

const FEATURES = [
  {
    icon: FileUp,
    n: "01",
    title: "Drop a paper",
    line: "Claims, citations and the bibliography are pulled out, page by page.",
    tone: "bg-lavender",
  },
  {
    icon: ScanSearch,
    n: "02",
    title: "We trace the source",
    line: "Each reference is matched to the real publication and its open-access text.",
    tone: "bg-coral-soft",
  },
  {
    icon: ShieldCheck,
    n: "03",
    title: "You see the evidence",
    line: "A verdict, a confidence level and the exact passage behind it.",
    tone: "bg-mint",
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
        <div className="absolute inset-0 grid-lines opacity-60" aria-hidden />
        <div className="absolute -right-20 top-10 h-56 w-56 rounded-full bg-lavender/60 blur-2xl" aria-hidden />

        <div className="relative mx-auto grid w-full max-w-6xl items-center gap-12 px-4 pb-14 pt-12 sm:px-6 lg:grid-cols-[1.02fr_0.98fr] lg:pb-20 lg:pt-16">
          <div className="animate-rise">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 bg-coral ring-2 ring-ink" />
              <span className="label-mono text-ink/70">Scientific claim verification</span>
            </div>

            <h1 className="display mt-5 text-[42px] leading-[0.9] sm:text-6xl lg:text-[76px]">
              Citations
              <br />
              aren't&nbsp;
              <span className="relative inline-block bg-violet px-2 text-white">
                proof
                <span className="absolute -bottom-2 -right-2 -z-10 h-full w-full border-2 border-ink bg-coral" />
              </span>
              .
            </h1>

            <p className="mt-6 max-w-md text-[14px] leading-relaxed text-ink/70">
              CiteVerify finds the paper behind each citation, reads it, and tells you whether it really
              supports the claim.
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

            <dl className="mt-9 flex flex-wrap items-center gap-x-7 gap-y-3">
              {STATS.map((stat) => (
                <div key={stat.label} className="flex items-baseline gap-2">
                  <dt className="font-display text-2xl leading-none">{stat.value}</dt>
                  <dd className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate">{stat.label}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* collage */}
          <div className="relative mx-auto h-[410px] w-full max-w-[440px] animate-rise sm:h-[440px] [animation-delay:120ms]">
            <div className="absolute inset-4 rotate-[-4deg] border-2 border-ink bg-lavender" aria-hidden />

            <div className="group absolute right-0 top-2 w-[88%] rotate-[2deg] border-2 border-ink bg-white p-5 shadow-block transition-transform duration-300 hover:rotate-0 hover:-translate-y-1">
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                <span>Claim 04</span>
                <span className="border border-ink/20 px-1.5 py-0.5">p. 3</span>
              </div>
              <p className="mt-3 text-[15px] font-semibold leading-snug">
                “A randomized trial found the app improved test scores by 30%.”
              </p>
              <div className="mt-4 flex items-center justify-between">
                <VerdictBadge verdict="partially_supported" size="sm" />
                <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">confidence · med</span>
              </div>
              <p className="mt-3 border-t-2 border-line pt-3 text-[11.5px] leading-relaxed text-slate">
                The paper reports improvement in a small pilot, but no 30% increase.
              </p>
            </div>

            <div className="group absolute bottom-1 left-0 w-[80%] rotate-[-2deg] border-2 border-ink bg-violet p-5 text-white shadow-block transition-transform duration-300 hover:rotate-0 hover:-translate-y-1">
              <Quote className="h-5 w-5 text-white/70" />
              <p className="mt-2 text-[13px] font-medium leading-snug">
                “Participants in the intervention arm improved, although the study was a small pilot.”
              </p>
              <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.14em] text-white/60">
                verbatim · results section
              </p>
            </div>

            <img
              src="/logo.png"
              alt=""
              className="absolute -bottom-3 right-2 h-14 w-14 rotate-6 border-2 border-ink object-cover shadow-block-sm transition-transform duration-300 hover:rotate-0"
            />
            <span className="absolute left-8 top-10 h-6 w-6 rotate-12 border-2 border-ink bg-coral" aria-hidden />
            <span className="absolute right-10 bottom-28 h-3 w-3 rounded-full bg-ink" aria-hidden />
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="mx-auto w-full max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-4 sm:grid-cols-3">
          {FEATURES.map(({ icon: Icon, n, title, line, tone }) => (
            <article
              key={title}
              className="group relative border-2 border-ink bg-white p-5 transition-all duration-200 hover:-translate-x-[3px] hover:-translate-y-[3px] hover:shadow-block"
            >
              <div className="flex items-start justify-between">
                <span className={`flex h-11 w-11 items-center justify-center border-2 border-ink ${tone} transition-transform duration-200 group-hover:-rotate-6`}>
                  <Icon className="h-5 w-5" />
                </span>
                <span className="font-mono text-[10px] text-slate">{n}</span>
              </div>
              <h2 className="mt-5 font-display text-lg uppercase">{title}</h2>
              <p className="mt-2 text-[12.5px] leading-relaxed text-slate">{line}</p>
              <span className="mt-4 flex items-center gap-1 font-mono text-[9.5px] uppercase tracking-[0.12em] text-violet opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                Explore <ArrowRight className="h-3 w-3" />
              </span>
            </article>
          ))}
        </div>
      </section>

      {/* VERDICTS */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-14 sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-ink pb-3">
          <h2 className="display text-xl sm:text-2xl">Six honest verdicts</h2>
          <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
            “unsupported” ≠ “false”
          </p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {VERDICT_ORDER.map((verdict) => (
            <span
              key={verdict}
              className="transition-transform duration-150 hover:-translate-y-1 hover:scale-[1.03]"
            >
              <VerdictBadge verdict={verdict} size="lg" />
            </span>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-4 sm:px-6">
        <div className="relative overflow-hidden border-2 border-ink bg-ink px-6 py-10 text-white sm:px-10">
          <div className="pointer-events-none absolute -right-8 -top-10 h-40 w-40 rounded-full border-2 border-lavender/30 bg-violet/40 blur-[1px]" aria-hidden />
          <div className="pointer-events-none absolute bottom-6 right-24 h-10 w-10 rotate-12 bg-coral" aria-hidden />
          <div className="relative flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <h2 className="display text-2xl sm:text-4xl">
                Check the evidence.
                <br />
                <span className="text-lavender">Not just the reference.</span>
              </h2>
              <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.14em] text-white/50">
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
