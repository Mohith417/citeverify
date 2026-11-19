import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

export function Logo({ light = false, size = 36 }: { light?: boolean; size?: number }) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2.5" aria-label="CiteVerify home">
      <img
        src="/logo.png"
        alt=""
        style={{ width: size, height: size }}
        className="shrink-0 border-2 border-ink object-cover transition-all duration-500 ease-smooth group-hover:-rotate-6 group-hover:scale-105 group-hover:shadow-block-xs"
      />
      <span
        className={cn(
          "font-display text-[17px] uppercase leading-none tracking-[-0.02em]",
          light ? "text-paper" : "text-ink",
        )}
      >
        Cite<span className="text-violet transition-colors duration-300 group-hover:text-coral">Verify</span>
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
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);

  // Drop a PDF anywhere in the app and it starts verifying: the header button
  // used to duplicate the hero and CTA upload links, this replaces it.
  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file && file.name.toLowerCase().endsWith(".pdf")) {
      navigate("/upload", { state: { file } });
    }
  }

  return (
    <div
      className="flex min-h-screen flex-col"
      onDragOver={(event) => {
        if (Array.from(event.dataTransfer.types).includes("Files")) {
          event.preventDefault();
          setDragging(true);
        }
      }}
      onDragLeave={(event) => {
        if (event.relatedTarget === null) setDragging(false);
      }}
      onDrop={handleDrop}
    >
      {dragging ? (
        <div className="pointer-events-none fixed inset-0 z-50 grid place-items-center bg-ink/75 p-6 text-paper">
          <div className="border-2 border-paper px-10 py-8 text-center">
            <p className="display text-3xl sm:text-4xl">Drop to verify</p>
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.16em] text-paper/60">
              one text-based PDF · max 20 MB
            </p>
          </div>
        </div>
      ) : null}
      <div className="overflow-hidden border-b-2 border-ink bg-ink py-1.5 text-paper">
        <div className="flex w-max animate-marquee items-center gap-8 hover-pause">
          {[0, 1].map((copy) => (
            <div key={copy} className="flex shrink-0 items-center gap-8">
              {TICKER.map((item) => (
                <span key={item} className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.2em]">
                  <span className="h-1 w-1 rotate-45 bg-coral" />
                  {item}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b-2 border-ink bg-paper/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-7 md:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "font-mono text-[13px] uppercase tracking-[0.12em] transition-colors duration-200",
                    isActive || location.pathname.startsWith(item.to)
                      ? "link-line font-semibold text-ink after:scale-x-100"
                      : "link-line text-ink/65 hover:text-ink",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <span className="hidden shrink-0 items-center gap-2 border-2 border-ink/15 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-ink/55 lg:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-mint ring-1 ring-ink/40" />
            Drag a PDF anywhere
          </span>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-16 border-t-2 border-ink bg-ink text-paper">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <Logo light />
            <p className="max-w-xs text-[12px] leading-relaxed text-paper/55">
              Checks whether cited research actually supports the claim — and shows the passage that
              decides it.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[10.5px] uppercase tracking-[0.14em] text-paper/55">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="link-line transition-colors duration-200 hover:text-paper"
              >
                {item.label}
              </Link>
            ))}
            <span className="hidden h-4 w-px bg-paper/20 sm:block" />
            <span>Crossref · OpenAlex · Europe PMC</span>
          </div>
        </div>
        <div className="border-t border-paper/15 px-4 py-3 text-center font-mono text-[10px] uppercase tracking-[0.16em] text-paper/40">
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
        <p className="label-mono flex items-center gap-2">
          <span className="h-2 w-2 rotate-45 bg-coral" />
          {eyebrow}
        </p>
        <h1 className="display text-3xl sm:text-[38px]">{title}</h1>
        {description ? (
          <p className="max-w-xl text-[13px] leading-relaxed text-slate">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
