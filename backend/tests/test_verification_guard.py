from app.services.ai_verifier import quote_in_source
from app.services.evidence_retrieval import retrieve_relevant_passages, split_into_paragraphs
from app.services.fulltext_retriever import safe_url


SOURCE = (
    "Participants in the intervention arm improved their reading scores compared with the "
    "waiting-list control group, although the study was a small pilot with 42 students."
)


def test_quote_must_exist_in_source():
    assert quote_in_source("the study was a small pilot with 42 students", SOURCE)
    assert not quote_in_source("test scores improved by 30% across all schools", SOURCE)


def test_quote_guard_tolerates_linebreak_hyphenation():
    assert quote_in_source("waiting-list control group", SOURCE)
    assert quote_in_source("waiting-list control group", SOURCE.replace("waiting-list", "waiting-\nlist"))


def test_ssrf_guard_blocks_local_and_non_http_targets():
    assert safe_url("http://127.0.0.1:8000/admin") is None
    assert safe_url("http://localhost/secret") is None
    assert safe_url("file:///etc/passwd") is None
    assert safe_url("https://user:pass@example.org/paper.pdf") is None


def test_paragraph_split_keeps_section_and_assigns_ids():
    text = (
        "Abstract\n\nThis study evaluates a mobile learning application in higher education "
        "settings with a randomised design and a waiting-list control group.\n\n"
        "Results\n\nStudents in the intervention group improved their reading scores, while the "
        "control group stayed stable over the same eight week period of the trial."
    )
    paragraphs = split_into_paragraphs(text, source_title="A mobile learning trial")
    assert paragraphs
    sections = {p.source_section for p in paragraphs}
    assert "Results" in sections
    assert all(p.paragraph_id for p in paragraphs)


def test_retrieval_prefers_the_relevant_paragraph_and_normalises_scores():
    paragraphs = split_into_paragraphs(
        "Introduction\n\nMobile applications are increasingly used in classrooms around the world "
        "and teachers report mixed experiences with them in practice.\n\n"
        "Results\n\nReading comprehension scores increased significantly for students who used the "
        "mobile application, with an effect size of 0.4 in the intervention group.",
        source_title="Trial",
    )
    ranked = retrieve_relevant_passages("The app increased reading comprehension scores", paragraphs, top_k=2)
    assert ranked
    assert "reading comprehension" in ranked[0][0].text.lower()
    assert all(0.0 <= score <= 1.0 for _, score in ranked)
