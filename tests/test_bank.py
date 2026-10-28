from collections import Counter
from pathlib import Path

from jobbot.assessment import dimension_key, load_bank

ROOT = Path(__file__).resolve().parent.parent
PER_DIMENSION = {"valores": 2, "interesses": 3, "personalidade": 3, "ancoras": 2, "estilo": 2}


def test_bank_loads():
    assert load_bank()


def test_counts_per_dimension():
    counts = Counter(dimension_key(i) for i in load_bank())
    assert len(counts) == 36
    for key, n in counts.items():
        assert n == PER_DIMENSION[key.split(".")[0]], key


def test_every_personality_dimension_has_reverse_items():
    bank = [i for i in load_bank() if i.layer == "personalidade"]
    for dim in {i.dimension for i in bank}:
        assert any(i.reverse for i in bank if i.dimension == dim), dim


def test_at_least_ten_twin_pairs_across_layers():
    twins = [i for i in load_bank() if i.twin]
    assert len(twins) >= 10
    assert {i.layer for i in twins} >= {"valores", "personalidade"}


def test_twin_stays_in_the_same_dimension():
    by_id = {i.id: i for i in load_bank()}
    for i in by_id.values():
        if i.twin:
            assert dimension_key(by_id[i.twin]) == dimension_key(i), i.id


def test_ids_and_texts_unique():
    bank = load_bank()
    assert len({i.id for i in bank}) == len(bank)
    assert len({i.text for i in bank}) == len(bank)


def test_total_items_fit_time_budget():
    assert len(load_bank()) <= 90


def test_sources_doc_mentions_ipip_and_originals():
    text = (ROOT / "references" / "assessment-sources.md").read_text(encoding="utf-8")
    assert "IPIP" in text and "original" in text.lower()


def test_no_proprietary_names_in_items():
    for i in load_bank():
        assert not any(w in i.text for w in ("MBTI", "Myers", "16PF")), i.id
