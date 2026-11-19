import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Button } from "./ui";
import { cn } from "@/lib/utils";

export function Logo({ light = false, size = 36 }: { light?: boolean; size?: number }) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5" aria-label="CiteVerify home">
      <img
        src="/logo.png"
        alt=""
        style={{ width: size, height: size }}
        className="shrink-0 border-2 border-ink object-cover transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105"
      />
      <span
        className={cn(
          "font-display text-[17px] uppercase leading-none tracking-[-0.02em]",
          light ? "text-white" : "text-ink",
        )}
      >
        Cite<span className="text-violet group-hover:text-coral">Verify</span>
      </span>
    </Link>
  );
}

const NAV = [
  { to: "/upload", label: "Verify" },
  { to: "/library", label: "History" },
  { to: "/method", label: "Method" },
];

const TICKER = [
  "Evidence-backed verification",
  "No fabricated sources",
  "Every finding open to review",
  "Open-access full text only",
];

export function Layout() {
  const location = useLocation();
  return (
    <div className="flex min-h-screen flex-col">
      <div className="overflow-hidden border-b-2 border-ink bg-ink py-1.5 text-white">
        <div className="flex w-max animate-marquee items-center gap-8 hover-pause">
          {[0, 1].map((copy) => (
            <div key={copy} className="flex shrink-0 items-center gap-8">
              {TICKER.map((item) => (
                <span key={item} className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.2em]">
                  <span className="h-1 w-1 rounded-full bg-coral" />
                  {item}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b-2 border-ink bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "border-2 px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.12em] transition-colors",
                    isActive || location.pathname.startsWith(item.to)
                      ? "border-ink bg-ink text-white"
                      : "border-transparent text-ink/60 hover:border-ink hover:bg-white hover:text-ink",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <Link to="/upload">
            <Button size="sm">
              New analysis
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-16 border-t-2 border-ink bg-ink text-white">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <Logo light />
            <p className="max-w-xs text-[12px] leading-relaxed text-white/60">
              Checks whether cited research actually supports the claim — and shows the passage that decides it.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[10.5px] uppercase tracking-[0.12em] text-white/60">
            {NAV.map((item) => (
              <Link key={item.to} to={item.to} className="transition-colors hover:text-white">
                {item.label}
              </Link>
            ))}
            <span className="hidden h-4 w-px bg-white/20 sm:block" />
            <span>Crossref · OpenAlex · Europe PMC</span>
          </div>
        </div>
        <div className="border-t border-white/15 px-4 py-3 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-white/40">
          Automated verdicts stay open to human review
        </div>
      </footer>
    </div>
  );
}

export function PageHeading({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 border-b-2 border-ink pb-5 md:flex-row md:items-end md:justify-between">
      <div className="space-y-3">
        <p className="label-mono">{eyebrow}</p>
        <h1 className="display text-3xl sm:text-[38px]">{title}</h1>
        {description ? <p className="max-w-xl text-[13px] leading-relaxed text-slate">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
