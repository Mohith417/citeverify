from app.services.citation_extractor import (find_citations, map_citation, parse_references,
                                             split_reference_entries)

NUM = ("[1] Smith J, Lee K. Blood pressure control in adults. Hypertension. 2020;5:1-9. doi:10.1234/ABC.5\n"
       "[2] Wang L. Salt intake and stroke risk. Lancet. 2019;3:10-20.")
APA = ("Smith, J., & Lee, K. (2020). Blood pressure control in adults. Hypertension, 5(1), 1-9.\n"
       "Wang, L. (2019). Salt intake and stroke risk. Lancet, 3, 10-20.")


def test_numbered_references():
    refs = parse_references(split_reference_entries(NUM))
    assert [r.label for r in refs] == ["1", "2"]
    assert refs[0].title == "Blood pressure control in adults"
    assert refs[0].year == 2020 and refs[0].doi == "10.1234/abc.5"
    assert refs[0].authors == ["Smith J", "Lee K"]
    assert refs[1].year == 2019 and not refs[1].flags


def test_author_year_references():
    refs = parse_references(split_reference_entries(APA))
    assert len(refs) == 2
    assert refs[0].authors == ["Smith, J.", "Lee, K."] and refs[0].year == 2020
    assert refs[0].title == "Blood pressure control in adults"
    assert refs[0].label == "Smith 2020"


def test_wrapped_numbered_entry():
    refs = parse_references(split_reference_entries("[1] Smith J. A long title about\nsomething. Journal. 2020.\n[2] Wang L. Other work here. Lancet. 2019."))
    assert len(refs) == 2 and "something" in refs[0].title


def test_duplicates_and_incomplete():
    txt = NUM + "\n[3] Smith J, Lee K. Blood pressure control in adults. Hypertension. 2020.\n[4] garbage"
    refs = parse_references(split_reference_entries(txt))
    assert "duplicate_reference" in refs[2].flags
    assert "incomplete_reference" in refs[3].flags


def test_numeric_citations():
    c = find_citations("A [1], B [2\u20134] and C [1, 3\u20135].")
    assert [x.numbers for x in c] == [[1], [2, 3, 4], [1, 3, 4, 5]]


def test_author_year_citations():
    c = find_citations("Seen (Smith et al., 2020; Wang, 2019) and Lee and Kim (2021) found it (January 2020).")
    got = [(x.author, x.year) for x in c]
    assert ("Smith", "2020") in got and ("Wang", "2019") in got and ("Lee", "2021") in got
    assert not any(a == "January" for a, _ in got)


def test_mapping():
    refs = parse_references(split_reference_entries(NUM))
    m = map_citation(find_citations("x [2] y")[0], refs)
    assert m[0].ref_index == 1 and m[0].status == "matched"
    assert map_citation(find_citations("x [9]")[0], refs)[0].status == "unmatched"
    ay = parse_references(split_reference_entries(APA))
    assert map_citation(find_citations("(Smith et al., 2020)")[0], ay)[0].ref_index == 0
    assert map_citation(find_citations("(Zhou, 2020)")[0], ay)[0].status == "unmatched"
    amb = parse_references(split_reference_entries(APA + "\nSmith, J. (2020). Another study of diets. Nutrition, 2, 4-8."))
    assert all(x.status == "ambiguous" for x in map_citation(find_citations("(Smith, 2020)")[0], amb))
