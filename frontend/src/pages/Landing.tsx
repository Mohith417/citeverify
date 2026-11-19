import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  FileUp,
  Quote,
  ScanSearch,
  ShieldCheck,
} from "lucide-react";
import { Button, VerdictBadge } from "@/components/ui";
import { VERDICT_META, VERDICT_ORDER, cn } from "@/lib/utils";
import type { Verdict } from "@/lib/types";

const STEPS = [
  {
    icon: FileUp,
    n: "01",
    title: "Drop a paper",
    line: "Every page is read, and the claims with their citation markers and bibliography are pulled out.",
    tone: "#DCD3E3",
  },
  {
    icon: ScanSearch,
    n: "02",
    title: "We trace the source",
    line: "Each reference is matched against Crossref, OpenAlex, Europe PMC and arXiv — only the real paper is accepted.",
    tone: "#F0DCD0",
  },
  {
    icon: ShieldCheck,
    n: "03",
    title: "You see the evidence",
    line: "The claim is compared with the source passage and gets a verdict, a confidence level and a quote.",
    tone: "#CBD7C6",
  },
];

const VERDICT_EXAMPLES: Record<string, { claim: string; reason: string }> = {
  supported: {
    claim: "“BERT obtains state-of-the-art results on eleven NLP tasks.”",
    reason: "The cited paper states the same result; the passage is quoted next to the verdict.",
  },
  partially_supported: {
    claim: "“A randomized trial found test scores improved by 30%.”",
    reason: "The source reports an improvement, but not that number — the direction holds, the size does not.",
  },
  unsupported: {
    claim: "“The method works on handwritten text without retraining.”",
    reason: "The source was read and never establishes this; the claim may still be true elsewhere.",
  },
  contradictory: {
    claim: "“Attention heads are only useful in the final layer.”",
    reason: "The paper reports the opposite finding — the strongest kind of flag, still open to review.",
  },
  potentially_outdated: {
    claim: "“This remains the largest public benchmark for the task.”",
    reason: "The source was current when written; newer work now reports larger results.",
  },
  insufficient_evidence: {
    claim: "“Users prefer personalised recourse plans.”",
    reason: "No citation, or no accessible open text — so nothing is asserted in either direction.",
  },
};

const STATS = [
  { value: "8", label: "research APIs" },
  { value: "6", label: "verdicts" },
  { value: "100%", label: "reviewable" },
];

export function Landing() {
  const [stage, setStage] = useState(0);
  const [verdict, setVerdict] = useState<Verdict>("partially_supported");

  useEffect(() => {
    const timer = window.setInterval(() => setStage((s) => (s + 1) % STEPS.length), 7000);
    return () => window.clearInterval(timer);
  }, []);

  const example = VERDICT_EXAMPLES[verdict] ?? VERDICT_EXAMPLES.partially_supported;

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

      {/* STEPS — click or hover a stage to see it happen */}
      <section className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3 pb-4">
          <h2 className="display text-2xl sm:text-3xl">How a check runs</h2>
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate">
            Pick a step · watch it happen
          </span>
        </div>

        <div className="grid gap-5 border-t-2 border-ink pt-5 lg:grid-cols-[1fr_1fr] lg:gap-8">
          <div className="divide-y-2 divide-ink/10 border-y-2 border-ink">
            {STEPS.map(({ icon: Icon, ...step }, index) => {
              const active = stage === index;
              return (
                <button
                  key={step.n}
                  type="button"
                  onMouseEnter={() => setStage(index)}
                  onFocus={() => setStage(index)}
                  onClick={() => setStage(index)}
                  aria-pressed={active}
                  className={cn(
                    "group flex w-full items-start gap-4 px-3 py-5 text-left transition-colors duration-200 sm:px-4",
                    active ? "bg-white" : "hover:bg-white/60",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center border-2 border-ink transition-all duration-300 ease-smooth",
                      active ? "-rotate-6 scale-105" : "group-hover:-rotate-3",
                    )}
                    style={{ backgroundColor: step.tone }}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline gap-3">
                      <span className="font-mono text-[10px] tracking-[0.18em] text-slate">{step.n}</span>
                      <span className="display text-xl leading-tight sm:text-2xl">{step.title}</span>
                    </span>
                    <span
                      className={cn(
                        "mt-1 block text-[12.5px] leading-relaxed text-ink/60 transition-all duration-300",
                        active ? "opacity-100" : "opacity-0 sm:opacity-60",
                      )}
                    >
                      {step.line}
                    </span>
                  </span>
                  <ArrowUpRight
                    className={cn(
                      "mt-2 h-4 w-4 shrink-0 transition-all duration-300",
                      active ? "rotate-45 text-violet" : "text-slate",
                    )}
                  />
                </button>
              );
            })}
          </div>

          <div className="relative min-h-[280px] overflow-hidden border-2 border-ink bg-white p-5">
            <div
              className="pointer-events-none absolute inset-0 stripes opacity-[0.35]"
              aria-hidden
            />
            <div key={stage} className="relative animate-rise space-y-4">
              {stage === 0 ? (
                <>
                  <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.14em] text-slate">
                    <span>reading · page 3 of 15</span>
                    <span className="border border-ink/20 px-1.5 py-0.5">PDF</span>
                  </div>
                  <p className="text-[13px] font-semibold">attention_is_all_you_need.pdf</p>
                  <div className="h-2 w-full border border-ink bg-paper">
                    <div className="h-full w-1/3 bg-violet transition-all duration-700" />
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {["claim · p.1", "marker [3]", "marker [12]", "bibliography"].map((chip) => (
                      <span
                        key={chip}
                        className="border border-ink/20 bg-paper px-2 py-1 font-mono text-[9.5px] uppercase tracking-[0.1em] text-ink/70"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                  <p className="pt-1 text-[12px] leading-relaxed text-slate">
                    16 claims and 40 references found — nothing is invented, only read.
                  </p>
                </>
              ) : null}

              {stage === 1 ? (
                <>
                  <div className="border border-ink/15 bg-paper p-3">
                    <p className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-slate">
                      reference [12]
                    </p>
                    <p className="mt-1 text-[12px] leading-snug text-ink/70">
                      Vaswani et al. Attention is all you need. NeurIPS, 2017.
                    </p>
                  </div>
                  <div className="flex justify-center text-slate">
                    <ArrowRight className="h-4 w-4 rotate-90" />
                  </div>
                  <div className="border-2 border-ink bg-white p-3 shadow-block-sm">
                    <p className="flex items-center gap-2 font-mono text-[9.5px] uppercase tracking-[0.12em] text-emerald-800">
                      <Check className="h-3.5 w-3.5" /> matched · arXiv + Crossref
                    </p>
                    <p className="mt-1.5 text-[13px] font-semibold leading-snug">
                      Attention Is All You Need
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-slate">2017 · open-access full text</p>
                  </div>
                  <p className="text-[12px] leading-relaxed text-slate">
                    Six providers are queried; a title that does not match is never accepted.
                  </p>
                </>
              ) : null}

              {stage === 2 ? (
                <>
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-[13px] font-semibold leading-snug">
                      “Attention lets the model weigh every other token when encoding a word.”
                    </p>
                    <VerdictBadge verdict="supported" size="sm" />
                  </div>
                  <div className="border-l-2 border-violet bg-lavender-soft p-3">
                    <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-violet">
                      source · §3.2
                    </p>
                    <p className="mt-1 flex gap-2 text-[12px] leading-relaxed text-ink/75">
                      <Quote className="mt-0.5 h-3.5 w-3.5 shrink-0 text-coral" />
                      “Attention allows the model to jointly attend to information from different
                      representation subspaces…”
                    </p>
                  </div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-slate">
                    confidence · high · still open to human review
                  </p>
                </>
              ) : null}
            </div>
          </div>
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

        <div className="grid grid-cols-2 gap-[2px] border-2 border-ink bg-ink lg:grid-cols-3">
          {VERDICT_ORDER.map((item, index) => {
            const meta = VERDICT_META[item];
            const active = verdict === item;
            return (
              <button
                key={item}
                type="button"
                onClick={() => setVerdict(item)}
                onMouseEnter={() => setVerdict(item)}
                aria-pressed={active}
                className={cn(
                  "group relative p-4 text-left transition-colors duration-200 sm:p-5",
                  active ? "bg-white" : "bg-paper hover:bg-white/70",
                )}
              >
                <span
                  className={cn(
                    "absolute right-4 top-4 font-mono text-[10px] transition-all duration-300 ease-smooth",
                    active ? "text-violet" : "text-ink/25 group-hover:-translate-y-0.5 group-hover:text-violet/60",
                  )}
                >
                  0{index + 1}
                </span>
                <VerdictBadge verdict={item} />
                <p className="mt-3 max-w-[26ch] text-[11.5px] leading-relaxed text-ink/60 transition-colors duration-200 group-hover:text-ink/80">
                  {meta.description}
                </p>
                <span
                  className={cn(
                    "absolute inset-x-0 bottom-0 h-1 origin-left bg-violet transition-transform duration-300 ease-smooth",
                    active ? "scale-x-100" : "scale-x-0",
                  )}
                />
              </button>
            );
          })}
        </div>

        <div
          key={verdict}
          className="mt-3 grid animate-rise gap-4 border-2 border-ink bg-white p-5 md:grid-cols-[1.15fr_0.85fr] md:gap-8"
        >
          <div>
            <p className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-slate">
              example claim
            </p>
            <p className="mt-2 text-[14px] font-semibold leading-snug">{example.claim}</p>
            <div className="mt-3 flex items-center gap-2">
              <VerdictBadge verdict={verdict} size="sm" />
              <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-slate">
                verdict
              </span>
            </div>
          </div>
          <div className="border-t-2 border-line pt-3 md:border-l-2 md:border-t-0 md:pl-6 md:pt-0">
            <p className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-slate">
              why it lands here
            </p>
            <p className="mt-2 text-[12.5px] leading-relaxed text-ink/70">{example.reason}</p>
            <Link
              to="/method"
              className="link-line mt-3 inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.12em] text-ink"
            >
              Method notes <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
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
