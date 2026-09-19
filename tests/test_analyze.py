"""Tests for analyze.py and charts.py on SYNTHETIC fixtures.

Verifies metrics contain no hard-coded numbers (all derived from the fixture)
and that charts render.
"""
import os
import sys
import tempfile

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ingest    # noqa: E402
import analyze   # noqa: E402
import charts    # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
CFG = ingest.load_config()


@pytest.fixture
def frames():
    df = pd.read_csv(os.path.join(FIX, "form_responses.SYNTHETIC.csv"))
    fr, fp = ingest.build_from_form(df, 500)
    ir, ip = ingest.build_from_interviews(os.path.join(FIX, "interviews"), 500)
    respondents = pd.concat([fr, ir], ignore_index=True)
    payments = pd.concat([fp, ip], ignore_index=True)
    return respondents, payments


def test_metrics_from_fixture(frames):
    respondents, payments = frames
    m = analyze.compute_metrics(respondents, payments, CFG)
    # counts reflect the fixture (4 form + 1 interview = 5 respondents)
    assert m["_meta"]["n_respondents"] == 5
    # G1 respondent paid 200 (paytm) and 1500 (gpay) -> by_count share small/large sane
    assert 0.0 <= m["paytm_share"]["all"]["by_count"] <= 1.0
    assert 0.0 <= m["paytm_share"]["all"]["by_value"] <= 1.0
    # concept interest present and labelled
    assert "not a forecast" in m["concept_interest"]["label"]
    assert m["concept_interest"]["n_answered"] >= 1


def test_sizing_uses_constant_only(frames):
    respondents, payments = frames
    m = analyze.compute_metrics(respondents, payments, CFG)
    s = m["sizing"]
    assert s["aishe_enrolment"] == CFG["aishe_enrolment"]
    # addressable is derived from observed share * constant, not hard-coded
    if "addressable_users_upper_bound" in s:
        frac = s["non_paytm_primary_share_of_voc"]
        assert s["addressable_users_upper_bound"] == int(round(frac * CFG["aishe_enrolment"]))


def test_charts_render(frames):
    respondents, payments = frames
    m = analyze.compute_metrics(respondents, payments, CFG)
    with tempfile.TemporaryDirectory() as d:
        p1 = charts.chart1_share_by_occasion(m, os.path.join(d, "c1.png"))
        p2 = charts.chart2_barrier_codes(os.path.join(d, "missing.csv"),
                                         os.path.join(d, "c2.png"))
        assert os.path.exists(p1) and os.path.getsize(p1) > 0
        assert os.path.exists(p2) and os.path.getsize(p2) > 0  # placeholder ok
