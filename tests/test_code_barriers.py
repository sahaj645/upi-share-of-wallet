"""Tests for src/code_barriers.py on SYNTHETIC fixtures."""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ingest         # noqa: E402
import code_barriers  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def test_match_codes_keywords():
    assert code_barriers.match_codes("cashback and habit")[0] in {"rewards_cashback", "habit_default"}
    assert code_barriers.match_codes("merchant qr is phonepe")[0] == "merchant_qr"
    assert code_barriers.match_codes("friends all use it for split")[0] == "peer_network"
    # empty answer -> no code
    assert code_barriers.match_codes("")[0] == ""


def test_final_code_blank_and_voc_only():
    df = pd.read_csv(os.path.join(FIX, "form_responses.SYNTHETIC.csv"))
    fr, _ = ingest.build_from_form(df, 500)
    ir, _ = ingest.build_from_interviews(os.path.join(FIX, "interviews"), 500)
    respondents = pd.concat([fr, ir], ignore_index=True)
    sheet = code_barriers.build_coding_sheet(respondents)
    # not-installed respondent (is_voc False) is excluded
    assert len(sheet) == (respondents["is_voc"] == True).sum()  # noqa: E712
    # final_code column exists and is entirely blank
    assert (sheet["final_code"] == "").all()
    assert "suggested_code" in sheet.columns
