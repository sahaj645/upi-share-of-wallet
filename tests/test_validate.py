"""Tests for src/validate.py check logic (no real deliverables needed)."""
import os
import sys
import tempfile

from openpyxl import Workbook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import validate  # noqa: E402

CFG = {"team_name": "T", "small_ticket_max": 500, "aishe_enrolment": 45000000,
       "paths": {"metrics": "outputs/metrics.json", "workbook_out": "deliverables"}}


def _make_voc(path, n_voc, groups, n_indepth):
    wb = Workbook()
    ws = wb.active
    ws.title = "VOC Collection"
    ws.append(["VOC ID", "Group", "Interview type"])
    for i in range(n_voc):
        g = groups[i % len(groups)]
        it = "In-depth" if i < n_indepth else "Survey"
        ws.append([f"V{i:03d}", g, it])
    wb.save(path)


def test_gate_passes_on_good_workbook():
    with tempfile.TemporaryDirectory() as d:
        _make_voc(os.path.join(d, "T_VOC.xlsx"), 55, ["G1", "G2", "G3"], 12)
        # PDF absent -> that one check fails, but VOC checks should pass
        results = dict((n, ok) for n, ok, _ in validate.run_checks(d, {}, CFG))
        assert results["≥50 unique VOCs"] is True
        assert results["All groups G1/G2/G3 present"] is True
        assert results["≥10 in-depth interviews"] is True


def test_gate_flags_missing_group_and_low_counts():
    with tempfile.TemporaryDirectory() as d:
        _make_voc(os.path.join(d, "T_VOC.xlsx"), 10, ["G1", "G2"], 2)
        results = dict((n, ok) for n, ok, _ in validate.run_checks(d, {}, CFG))
        assert results["≥50 unique VOCs"] is False
        assert results["All groups G1/G2/G3 present"] is False
        assert results["≥10 in-depth interviews"] is False


def test_number_whitelist_and_pii():
    allowed = validate._allowed_numbers({"paytm_share": {"all": {"by_value": 0.42}}}, CFG)
    assert "42%" in allowed          # 0.42 -> 42%
    assert "500" in allowed          # structural constant
    assert validate.EMAIL.search("reach me at a@b.com")
    assert validate.PHONE.search("call 9876543210")
