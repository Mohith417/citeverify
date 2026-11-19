from .claim_extractor import claim_extractor
from .ai_verifier import ai_verifier
from .evidence_retrieval import (
    split_into_paragraphs,
    retrieve_relevant_passages,
    build_faiss_index,
    search_faiss,
    EvidenceParagraph,
)
from .fulltext_retriever import retrieve_full_text, FullTextResult
from .grobid_service import grobid_service
from .misleading_reference_detector import detect_issues, summarize_flags
from .report_generator import generate_report
from .research_provider import NormalizedPaper, ResearchProvider
from .semantic_scholar_provider import SemanticScholarProvider
from .unpaywall_provider import UnpaywallProvider
from .arxiv_provider import ArxivProvider
from .research_discovery import research_discovery, ResearchDiscovery

__all__ = [
    "claim_extractor",
    "ai_verifier",
    "split_into_paragraphs",
    "retrieve_relevant_passages",
    "build_faiss_index",
    "search_faiss",
    "EvidenceParagraph",
    "retrieve_full_text",
    "FullTextResult",
    "grobid_service",
    "detect_issues",
    "summarize_flags",
    "generate_report",
    "NormalizedPaper",
    "ResearchProvider",
    "SemanticScholarProvider",
    "UnpaywallProvider",
    "ArxivProvider",
    "research_discovery",
    "ResearchDiscovery",
]
