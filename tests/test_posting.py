import pytest

from jobbot.posting import Posting, posting_from_dict


def test_posting_valid_and_defaults():
    p = posting_from_dict({"title": "Analista de Dados", "company": "Acme", "skills": ["SQL"]})
    assert p == Posting("Analista de Dados", "Acme", ["SQL"])


def test_posting_full():
    p = posting_from_dict({"title": "T", "company": "C", "skills": ["a"], "salary": 6000,
                           "modality": "hibrido", "contract": "CLT", "url": "https://x"})
    assert (p.salary, p.modality, p.contract, p.url) == (6000, "hibrido", "CLT", "https://x")


@pytest.mark.parametrize("bad,match", [
    ({"title": "T", "extra": 1}, "extra"),
    ({"company": "C"}, "title"),
    ({"title": ""}, "title"),
    ({"title": "T", "skills": ["a", 1]}, "skills"),
    ({"title": "T", "skills": "SQL"}, "skills"),
    ({"title": "T", "salary": "5 mil"}, "salary"),
    ({"title": "T", "salary": True}, "salary"),
    ({"title": "T", "modality": "home"}, "modality"),
    ({"title": "T", "contract": "estagio"}, "contract"),
])
def test_posting_rejects_bad_input(bad, match):
    with pytest.raises(ValueError, match=match):
        posting_from_dict(bad)


def test_posting_must_be_a_map():
    with pytest.raises(ValueError):
        posting_from_dict(["x"])


def test_salary_estimate_needs_a_source_and_an_integer():
    from jobbot.posting import posting_from_dict
    ok = posting_from_dict({"title": "T", "salary_estimate": 5000, "salary_source": "Glassdoor, 2026-10-26"})
    assert ok.salary_estimate == 5000 and ok.salary is None
    with pytest.raises(ValueError, match="salary_source"):
        posting_from_dict({"title": "T", "salary_estimate": 5000})
    with pytest.raises(ValueError, match="inteiro"):
        posting_from_dict({"title": "T", "salary_estimate": "5k", "salary_source": "x"})
