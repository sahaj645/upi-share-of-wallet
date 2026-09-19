"""Test build_summary.py generates a valid 2-section docx from fixture metrics."""
import os
import sys
import tempfile

import pandas as pd
from docx import Document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ingest         # noqa: E402
import analyze        # noqa: E402
import build_summary  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
CFG = ingest.load_config()


def _metrics():
    df = pd.read_csv(os.path.join(FIX, "form_responses.SYNTHETIC.csv"))
    fr, fp = ingest.build_from_form(df, 500)
    return analyze.compute_metrics(fr, fp, CFG)


def test_summary_docx_built():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "T_ExecSummary.docx")
        build_summary.build_summary(
            _metrics(), verification_path=os.path.join(d, "missing.md"),
            quotes_path=os.path.join(d, "missing.md"),
            charts_dir=os.path.join(d, "charts"), out_docx=out, team="T")
        assert os.path.exists(out)
        doc = Document(out)
        text = "\n".join(p.text for p in doc.paragraphs)
        assert "not a forecast" in text.lower()
        # a page break separates the two pages
        xml = doc.element.xml
        assert "w:br" in xml and "page" in xml


def test_verified_claims_parsing():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "ver.md")
        open(p, "w", encoding="utf-8").write(
            "| # | Claim | Status | val | ev |\n"
            "|---|-------|--------|-----|----|\n"
            "| 1 | Secondary user in UPI Circle | VERIFIED | yes | e1 |\n"
            "| 2 | Monthly cap 15000 | NOT_FOUND |  |  |\n")
        claims = build_summary.verified_claims(p)
        assert claims == ["Secondary user in UPI Circle"]
