from enum import Enum


class ProcessingStatus(str, Enum):
    uploaded = "uploaded"
    extracting = "extracting"
    searching_references = "searching_references"
    retrieving_evidence = "retrieving_evidence"
    comparing_claims = "comparing_claims"
    generating_report = "generating_report"
    completed = "completed"
    failed = "failed"
    needs_review = "needs_review"


class Verdict(str, Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    unsupported = "unsupported"
    contradictory = "contradictory"
    potentially_outdated = "potentially_outdated"
    insufficient_evidence = "insufficient_evidence"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class MatchingStatus(str, Enum):
    pending = "pending"
    matched = "matched"
    ambiguous = "ambiguous"
    not_found = "not_found"
    incomplete = "incomplete"


class FulltextAvailability(str, Enum):
    none = "none"
    abstract_only = "abstract_only"
    full_text = "full_text"


class ReviewedStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    overridden = "overridden"
