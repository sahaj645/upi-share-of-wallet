"""Tests for src/ingest.py — group assignment and payment reshaping.

Runs on SYNTHETIC fixtures only. No real data is touched.
"""
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ingest  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
SMALL_MAX = 500


# ---- group assignment -----------------------------------------------------
@pytest.mark.parametrize("primary,paytm90,installed,expected", [
    ("Paytm",   "No",  "Yes", "G1"),   # paytm primary -> G1 regardless of 90d
    ("Paytm",   "Yes", "Yes", "G1"),
    ("PhonePe", "Yes", "Yes", "G2"),   # other primary + used in 90d
    ("GPay",    "No",  "Yes", "G3"),   # other primary + not in 90d
    ("PhonePe", "Yes", "No",  None),   # not installed -> rates only
])
def test_assign_group(primary, paytm90, installed, expected):
    assert ingest.assign_group(primary, paytm90, installed) == expected


# ---- form ingestion -------------------------------------------------------
@pytest.fixture
def form_out():
    df = pd.read_csv(os.path.join(FIX, "form_responses.SYNTHETIC.csv"))
    return ingest.build_from_form(df, SMALL_MAX)


def test_form_group_counts(form_out):
    resp, _ = form_out
    groups = resp.set_index("voc_id")["group"].to_dict()
    # 4 rows: G1, G2, G3, and a not-installed (None)
    assert list(resp["group"]).count("G1") == 1
    assert list(resp["group"]).count("G2") == 1
    assert list(resp["group"]).count("G3") == 1
    assert resp["group"].isna().sum() == 1


def test_not_installed_is_not_voc(form_out):
    resp, _ = form_out
    not_installed = resp[resp["group"].isna()].iloc[0]
    assert not_installed["is_voc"] is False or not_installed["is_voc"] == False  # noqa: E712


def test_payments_reshaped_with_is_small(form_out):
    _, pay = form_out
    # G1 respondent has a 200 (small) and a 1500 (large) payment
    assert (pay["amount"] == 200).any()
    assert (pay["amount"] == 1500).any()
    small = pay[pay["amount"] == 200].iloc[0]
    large = pay[pay["amount"] == 1500].iloc[0]
    assert bool(small["is_small"]) is True
    assert bool(large["is_small"]) is False


def test_no_pii_columns(form_out):
    resp, _ = form_out
    for col in resp.columns:
        assert not ingest.PII_PATTERNS.search(col), f"PII column leaked: {col}"


# ---- interview ingestion --------------------------------------------------
def test_interview_parses_and_reshapes():
    resp, pay = ingest.build_from_interviews(
        os.path.join(FIX, "interviews"), SMALL_MAX
    )
    assert len(resp) == 1
    row = resp.iloc[0]
    assert row["voc_id"] == "I001"
    assert row["is_indepth"] == True  # noqa: E712
    assert row["group"] == "G2"       # derived: PhonePe primary + paytm 90d yes
    assert len(pay) == 2
    assert bool(pay[pay["amount"] == 100].iloc[0]["is_small"]) is True
    assert bool(pay[pay["amount"] == 900].iloc[0]["is_small"]) is False
