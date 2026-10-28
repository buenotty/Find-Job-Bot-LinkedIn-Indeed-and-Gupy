from datetime import date

from jobbot.pdf import extract_text, render_pdf, sanitize, write_pdf
from jobbot.resume import ResumeContent, ResumeDoc, build_resume, doc_text
from tests.test_resume import person

TODAY = date(2026, 10, 25)


def norm(text):
    return " ".join(text.split())


def make_doc(summary="Analista de dados focada em automação."):
    content = ResumeContent(summary=summary, experience_bullets={"Loja Modelo": ["Automatizei relatórios em 30%"]})
    return build_resume(person(), content, ["Kafka"], TODAY)


def test_pdf_text_is_extractable_in_reading_order(tmp_path):
    doc = make_doc()
    write_pdf(doc, tmp_path / "a.pdf")
    text = norm(extract_text(tmp_path / "a.pdf"))
    fragments = [doc.name, "Resumo", doc.summary, "Experiência", doc.experiences[0]["title"], doc.experiences[0]["company"],
                 doc.experiences[0]["bullets"][0], "Competências", "Formação", "Certificações", "Idiomas"]
    position = -1
    for frag in fragments:
        found = text.find(norm(sanitize(frag)), position + 1)
        assert found > position, frag
        position = found


def test_dates_are_shown_as_month_and_year(tmp_path):
    write_pdf(make_doc(), tmp_path / "a.pdf")
    assert "fev/2021 - atual" in norm(extract_text(tmp_path / "a.pdf"))


def test_skill_groups_render_as_labelled_lines(tmp_path):
    from dataclasses import replace
    doc = replace(make_doc(), headline="Analista de dados", skill_groups=[("Dados", ["SQL", "Excel"]), ("Código", ["Python"])])
    write_pdf(doc, tmp_path / "a.pdf")
    text = norm(extract_text(tmp_path / "a.pdf"))
    assert "Analista de dados" in text and "Dados: SQL, Excel" in text and "Código: Python" in text


def test_accents_survive(tmp_path):
    doc = make_doc("Atenção à gestão de informações, ação e coração.")
    write_pdf(doc, tmp_path / "a.pdf")
    text = extract_text(tmp_path / "a.pdf")
    for word in ("Atenção", "gestão", "informações", "ação", "coração", "Experiência", "Competências"):
        assert word in text, word


def test_typographic_chars_mapped():
    assert sanitize("a – b • “c” d… e f") == 'a - b - "c" d... e f'


def test_non_latin1_never_crashes(tmp_path):
    doc = make_doc("Seta → e emoji 😀 no texto.")
    write_pdf(doc, tmp_path / "a.pdf")
    text = extract_text(tmp_path / "a.pdf")
    assert "Seta ? e emoji ? no texto." in norm(text)


def test_no_images_or_annotations(tmp_path):
    write_pdf(make_doc(), tmp_path / "a.pdf")
    from pypdf import PdfReader
    page = PdfReader(str(tmp_path / "a.pdf")).pages[0]
    assert "/Annots" not in page and list(page.images) == []


def test_single_page_for_short_and_multi_page_for_long(tmp_path):
    from pypdf import PdfReader
    write_pdf(make_doc(), tmp_path / "short.pdf")
    assert len(PdfReader(str(tmp_path / "short.pdf")).pages) == 1
    long_doc = ResumeDoc("Maria", "x", "", [{"title": "T", "company": "C", "period": "2020 - Atual",
                                             "bullets": [f"Item numero {i}" for i in range(150)]}], [], [], [], [])
    write_pdf(long_doc, tmp_path / "long.pdf")
    assert len(PdfReader(str(tmp_path / "long.pdf")).pages) > 1


def test_write_pdf_permissions_0600(tmp_path):
    write_pdf(make_doc(), tmp_path / "sub" / "a.pdf")
    assert (tmp_path / "sub" / "a.pdf").stat().st_mode & 0o777 == 0o600


def test_render_pdf_returns_pdf_bytes():
    assert render_pdf(make_doc()).startswith(b"%PDF")


def test_sanitize_folds_accents_outside_latin1_and_reports_lossy_chars():
    from jobbot.pdf import lossy_chars
    assert sanitize("Ĉ ŝ ﬁ") == "C s fi"
    assert lossy_chars("a ≥ b € c ≥ d 😀 ç") == ["≥", "€", "😀"]
    assert lossy_chars("só acentos e – travessão") == []
