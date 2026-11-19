import { clsx, type ClassValue } from "clsx";
import type { Confidence, Verdict } from "./types";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export const VERDICT_META: Record<
  Verdict,
  { label: string; short: string; className: string; dot: string; description: string }
> = {
  supported: {
    label: "Supported",
    short: "Supported",
    className: "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200",
    dot: "bg-emerald-500",
    description: "The retrieved research directly establishes the statement.",
  },
  partially_supported: {
    label: "Partly supported",
    short: "Partial",
    className: "bg-amber-50 text-amber-800 ring-1 ring-amber-200",
    dot: "bg-amber-500",
    description: "The main idea holds, but numbers, scope or details are not established.",
  },
  unsupported: {
    label: "Unsupported",
    short: "Unsupported",
    className: "bg-orange-50 text-orange-800 ring-1 ring-orange-200",
    dot: "bg-orange-500",
    description: "The accessible evidence does not establish the statement.",
  },
  contradictory: {
    label: "Contradictory",
    short: "Contradictory",
    className: "bg-rose-50 text-rose-800 ring-1 ring-rose-200",
    dot: "bg-rose-500",
    description: "The source reports findings that conflict with the statement.",
  },
  potentially_outdated: {
    label: "Potentially outdated",
    short: "Outdated?",
    className: "bg-yellow-50 text-yellow-800 ring-1 ring-yellow-200",
    dot: "bg-yellow-500",
    description: "Newer research is needed before this can be treated as current.",
  },
  insufficient_evidence: {
    label: "Insufficient evidence",
    short: "No evidence",
    className: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
    dot: "bg-slate-400",
    description: "No usable source evidence was retrieved, or no citation was attached.",
  },
};

export const VERDICT_ORDER: Verdict[] = [
  "supported",
  "partially_supported",
  "unsupported",
  "contradictory",
  "potentially_outdated",
  "insufficient_evidence",
];

export function verdictMeta(verdict: Verdict | null | undefined) {
  return verdict ? VERDICT_META[verdict] : VERDICT_META.insufficient_evidence;
}

export const CONFIDENCE_META: Record<Confidence, { label: string; bars: number }> = {
  low: { label: "Low confidence", bars: 1 },
  medium: { label: "Medium confidence", bars: 2 },
  high: { label: "High confidence", bars: 3 },
};

export function formatDate(value: string) {
  const date = new Date(value.endsWith("Z") ? value : `${value}Z`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortId(id: string) {
  return id.slice(0, 8).toUpperCase();
}

export function flagLabel(flag: string) {
  return flag.replaceAll("_", " ");
}

export const STAGES: Array<{ key: string; label: string; hint: string }> = [
  { key: "extracting", label: "Extract", hint: "Claims, citation markers and the reference list" },
  { key: "searching_references", label: "Retrieve", hint: "Original publications via Crossref, OpenAlex, Europe PMC, Semantic Scholar" },
  { key: "retrieving_evidence", label: "Evidence", hint: "Legal open-access full text and relevant passages" },
  { key: "comparing_claims", label: "Compare", hint: "Claim-by-claim comparison against the source findings" },
  { key: "generating_report", label: "Report", hint: "Flags, confidence and human-review items" },
  { key: "completed", label: "Ready", hint: "Verification report available" },
];

export function stageIndex(status: string) {
  const index = STAGES.findIndex((s) => s.key === status);
  return index === -1 ? 0 : index;
}
