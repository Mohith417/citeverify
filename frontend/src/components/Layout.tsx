import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ArrowUpRight, BookOpenCheck, ShieldCheck } from "lucide-react";
import { Button } from "./ui";
import { cn } from "@/lib/utils";

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5" aria-label="CiteVerify home">
      <span className="grid h-8 w-8 grid-cols-2 grid-rows-2 border-2 border-ink">
        <span className={cn("border-b border-r border-ink", light ? "bg-white" : "bg-violet")} />
        <span className={cn("border-b border-ink", light ? "bg-lavender" : "bg-coral")} />
        <span className={cn("border-r border-ink", light ? "bg-coral" : "bg-lavender")} />
        <span className={cn(light ? "bg-violet" : "bg-ink")} />
      </span>
      <span className={cn("font-display text-lg uppercase tracking-tight", light ? "text-white" : "text-ink")}>
        Cite<span className={light ? "text-lavender" : "text-violet"}>Verify</span>
      </span>
    </Link>
  );
}

const NAV = [
  { to: "/upload", label: "Verify a document" },
  { to: "/library", label: "Review history" },
  { to: "/method", label: "Method" },
];

export function Layout() {
  const location = useLocation();
  return (
    <div className="flex min-h-screen flex-col">
      <div className="border-b-2 border-ink bg-ink px-4 py-2 text-center text-[11px] font-medium tracking-wide text-white/90">
        An evidence-backed verification tool — every automated finding stays open to human review.
      </div>
      <header className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "px-3 py-2 text-sm font-medium transition-colors",
                    isActive || location.pathname.startsWith(item.to)
                      ? "text-ink underline decoration-violet decoration-2 underline-offset-8"
                      : "text-slate hover:text-ink",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/upload" className="hidden sm:block">
              <Button size="sm" variant="primary">
                New analysis
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t-2 border-ink bg-ink text-white">
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
          <div className="space-y-4">
            <Logo light />
            <p className="max-w-sm text-sm leading-relaxed text-white/70">
              CiteVerify checks whether cited research actually supports the claim being made — with the
              source passage, a confidence indicator and a review trail.
            </p>
            <div className="inline-flex items-center gap-2 border border-white/20 px-2.5 py-1 text-[11px] text-white/70">
              <ShieldCheck className="h-3.5 w-3.5" />
              Free and open research APIs only · no paywall bypassing
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/50">Product</p>
            {NAV.map((item) => (
              <Link key={item.to} to={item.to} className="block text-white/75 hover:text-white">
                {item.label}
              </Link>
            ))}
          </div>
          <div className="space-y-3 text-sm">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/50">Sources</p>
            <p className="text-white/75">Crossref · OpenAlex</p>
            <p className="text-white/75">Europe PMC · Semantic Scholar</p>
            <p className="text-white/75">Unpaywall · arXiv</p>
            <p className="pt-2 font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
              Built for academic trust
            </p>
          </div>
        </div>
        <div className="border-t border-white/10 px-4 py-4 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-white/40">
          CiteVerify · research integrity assistant · findings are not final academic judgments
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
    <div className="flex flex-col gap-4 border-b border-line pb-6 md:flex-row md:items-end md:justify-between">
      <div className="space-y-2">
        <p className="label-mono flex items-center gap-2">
          <BookOpenCheck className="h-3.5 w-3.5" />
          {eyebrow}
        </p>
        <h1 className="display text-2xl sm:text-3xl">{title}</h1>
        {description ? <p className="max-w-2xl text-sm leading-relaxed text-slate">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
