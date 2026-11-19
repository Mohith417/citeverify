"""Module 11: downloadable verification report (ReportLab).

The report is generated only from rows stored for the document: claims,
matched references, retrieved evidence passages and verdicts. Nothing is invented
and the disclaimer keeps every finding open to human review.
"""

from __future__ import annotations

import logging
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from ..models import Claim, Document, Evidence, Reference, Verification

logger = logging.getLogger(__name__)

INK = colors.HexColor("#171436")
VERDICT_COLORS = {
    "supported": "#0f7a4d",
    "partially_supported": "#a86a00",
    "unsupported": "#b3261e",
    "contradictory": "#b3261e",
    "potentially_outdated": "#8a4b00",
    "insufficient_evidence": "#5b5b6b",
}
VERDICT_LABELS = {
    "supported": "Supported",
    "partially_supported": "Partly supported",
    "unsupported": "Unsupported",
    "contradictory": "Contradictory",
    "potentially_outdated": "Potentially outdated",
    "insufficient_evidence": "Insufficient evidence",
}


def _p(text: str, style) -> Paragraph:
    return Paragraph(escape(str(text or "")), style)


class VerificationReportGenerator:
    def __init__(self, db: Session, document_id: str) -> None:
        self.db = db
        self.doc = db.get(Document, document_id)
        if self.doc is None:
            raise ValueError(f"Document {document_id} not found")
        base = getSampleStyleSheet()
        self.title = ParagraphStyle("CVTitle", parent=base["Title"], fontName="Helvetica-Bold",
                                    fontSize=22, leading=26, textColor=INK, alignment=0)
        self.subtitle = ParagraphStyle("CVSub", parent=base["Normal"], fontSize=10,
                                       leading=14, textColor=colors.HexColor("#4a4668"))
        self.heading = ParagraphStyle("CVH2", parent=base["Heading2"], fontName="Helvetica-Bold",
                                      fontSize=13, leading=16, textColor=INK, spaceBefore=10,
                                      spaceAfter=6)
        self.label = ParagraphStyle("CVLabel", parent=base["Normal"], fontName="Helvetica-Bold",
                                    fontSize=8.5, leading=11, textColor=colors.HexColor("#6b6b80"))
        self.body = ParagraphStyle("CVBody", parent=base["Normal"], fontSize=9.5, leading=13.5,
                                   textColor=colors.HexColor("#1c1c28"))
        self.small = ParagraphStyle("CVSmall", parent=base["Normal"], fontSize=8.5, leading=12,
                                    textColor=colors.HexColor("#3c3c4a"))

    # ------------------------------------------------------------------
    def generate(self, output_path: str) -> str:
        doc = BaseDocTemplate(
            output_path, pagesize=A4,
            leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
            title=f"CiteVerify Report - {self.doc.filename}", author="CiteVerify",
        )
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
        doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])

        story = []
        story += self._header()
        story += self._summary()
        story += self._claims()
        story += self._references()
        story += self._footer()
        doc.build(story)
        logger.info("Report generated: %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    def _header(self):
        s = [
            Paragraph("CiteVerify", self.title),
            Paragraph("Scientific Claim and Citation Verification Report", self.subtitle),
            Spacer(1, 6),
            HRFlowable(width="100%", thickness=1.2, color=INK),
            Spacer(1, 8),
            _p(f"Document: {self.doc.filename}", self.subtitle),
            _p(f"Uploaded: {self.doc.uploaded_at:%Y-%m-%d %H:%M} UTC" if self.doc.uploaded_at else "Uploaded: n/a", self.subtitle),
            _p(f"Pages: {self.doc.page_count}   Status: {self.doc.processing_status}", self.subtitle),
            Spacer(1, 8),
        ]
        return s

    def _counts(self):
        claims = self.db.query(Claim).filter(Claim.document_id == self.doc.id).all()
        refs = self.db.query(Reference).filter(Reference.document_id == self.doc.id).all()
        verdicts: dict[str, int] = {}
        review = 0
        for claim in claims:
            v = self.db.query(Verification).filter(Verification.claim_id == claim.id).first()
            if v:
                verdicts[v.verdict] = verdicts.get(v.verdict, 0) + 1
                review += int(bool(v.needs_human_review))
        return claims, refs, verdicts, review

    def _summary(self):
        claims, refs, verdicts, review = self._counts()
        matched = sum(1 for r in refs if r.matching_status == "matched")
        fulltext = sum(1 for r in refs if r.fulltext_availability == "full_text")
        rows = [
            ["Metric", "Value"],
            ["Claims extracted", str(len(claims))],
            ["Citations found in claims", str(sum(len(c.citation_markers or []) for c in claims))],
            ["References parsed", str(len(refs))],
            ["References matched to a publication", str(matched)],
            ["Open-access full texts retrieved", str(fulltext)],
        ]
        for key, label in VERDICT_LABELS.items():
            rows.append([label, str(verdicts.get(key, 0))])
        rows.append(["Flagged for human review", str(review)])

        table = Table(rows, colWidths=[110 * mm, 50 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f4fb")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8d5ea")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [Paragraph("Verification Summary", self.heading), table, Spacer(1, 8)]

    def _claims(self):
        story = [Paragraph("Claim-by-Claim Results", self.heading)]
        claims = (self.db.query(Claim).filter(Claim.document_id == self.doc.id)
                  .order_by(Claim.page_number.asc()).all())
        if not claims:
            return story + [_p("No claims were extracted from this document.", self.body)]

        for i, claim in enumerate(claims, start=1):
            v = self.db.query(Verification).filter(Verification.claim_id == claim.id).first()
            evidence = self.db.query(Evidence).filter(Evidence.claim_id == claim.id).all()
            links = [link for link in claim.reference_links if link.match_status == "matched"]
            ref = links[0].reference if links else None

            story.append(Paragraph(f"Claim {i}", self.heading))
            story.append(_p(claim.claim_text, self.body))
            story.append(Spacer(1, 3))
            story.append(_p(
                f"Page {claim.page_number if claim.page_number is not None else 'n/a'}  |  "
                f"Category: {claim.claim_category}  |  "
                f"Citations: {', '.join(claim.citation_markers) if claim.citation_markers else 'none'}",
                self.small,
            ))
            if ref:
                story.append(_p(
                    f"Matched source: {ref.matched_title or ref.title or 'not matched'} "
                    f"({ref.matched_year or ref.year or 'n/a'})", self.small))
                if ref.matched_doi or ref.doi:
                    story.append(_p(f"DOI: {ref.matched_doi or ref.doi}  |  Match: {ref.matching_status} "
                                    f"(confidence {ref.matching_confidence or 'n/a'})", self.small))
                if ref.matched_source_url:
                    story.append(Paragraph(
                        f'Source: <link href="{escape(ref.matched_source_url)}" color="#4b34f0">'
                        f'{escape(ref.matched_source_url)}</link>', self.small))
            else:
                story.append(_p("Matched source: none (no unambiguous reference match).", self.small))

            if v:
                color = VERDICT_COLORS.get(v.verdict, "#5b5b6b")
                story.append(Paragraph(
                    f'<font color="{color}"><b>{VERDICT_LABELS.get(v.verdict, v.verdict)}</b></font>'
                    f'  — confidence: {v.confidence_level}'
                    f'  — evidence basis: {v.evidence_basis.replace("_", " ")}', self.body))
                story.append(_p(v.explanation, self.body))
                if v.confidence_reason:
                    story.append(_p(f"Confidence reason: {v.confidence_reason}", self.small))
                if v.key_supporting_facts:
                    story.append(_p("Supporting facts: " + "; ".join(v.key_supporting_facts), self.small))
                if v.limitations:
                    story.append(_p("Limitations: " + "; ".join(v.limitations), self.small))
                story.append(_p(
                    f"Human review: {'required' if v.needs_human_review else 'not required'} "
                    f"({v.reviewed_status})", self.small))
            else:
                story.append(_p("Verdict: not verified in this run.", self.body))

            if evidence:
                story.append(_p("Evidence passages:", self.label))
                for ev in evidence[:3]:
                    snippet = ev.passage[:700] + ("…" if len(ev.passage) > 700 else "")
                    story.append(_p(f"“{snippet}”", self.body))
                    story.append(_p(
                        f"— {ev.source_section or 'section unknown'}"
                        f"{' (abstract only)' if ev.is_abstract_only else ''}"
                        f"{' · quote verified' if ev.quote_verified else ''}", self.small))
            if claim.flags:
                story.append(_p("Flags: " + ", ".join(claim.flags), self.small))
            story.append(Spacer(1, 10))
        return story

    def _references(self):
        story = [Paragraph("Reference Matching Detail", self.heading)]
        refs = self.db.query(Reference).filter(Reference.document_id == self.doc.id).all()
        if not refs:
            return story + [_p("No reference list was detected in this document.", self.body)]
        for ref in refs:
            story.append(_p(f"[{ref.ref_label or '—'}] {ref.reference_text[:300]}", self.body))
            story.append(_p(
                f"Status: {ref.matching_status}"
                f"  |  Full text: {ref.fulltext_availability.replace('_', ' ')}"
                f"  |  Matched title: {ref.matched_title or '—'}", self.small))
            if ref.flags:
                story.append(_p("Flags: " + ", ".join(ref.flags), self.small))
            story.append(Spacer(1, 5))
        return story

    def _footer(self):
        return [
            Spacer(1, 10),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cfcce0")),
            Spacer(1, 4),
            Paragraph(
                "Generated by CiteVerify. Verdicts are automated, evidence-backed indications — "
                "not final academic judgments. Every finding remains open to human review.",
                ParagraphStyle("footer", parent=self.small, fontSize=7.5, textColor=colors.HexColor("#6b6b80")),
            ),
        ]


def generate_report(db: Session, document_id: str, output_path: str) -> str:
    return VerificationReportGenerator(db, document_id).generate(output_path)
