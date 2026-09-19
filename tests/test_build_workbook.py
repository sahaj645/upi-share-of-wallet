"""Test build_workbook.py builds all sheets from SYNTHETIC fixtures."""
import os
import sys
import tempfile

import pandas as pd
import yaml
from openpyxl import load_workbook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ingest          # noqa: E402
import analyze         # noqa: E402
import build_workbook  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
CFG = ingest.load_config()


def test_workbook_sheets_and_rows():
    df = pd.read_csv(os.path.join(FIX, "form_responses.SYNTHETIC.csv"))
    fr, fp = ingest.build_from_form(df, 500)
    ir, ip = ingest.build_from_interviews(os.path.join(FIX, "interviews"), 500)
    respondents = pd.concat([fr, ir], ignore_index=True)
    payments = pd.concat([fp, ip], ignore_index=True)
    metrics = analyze.compute_metrics(respondents, payments, CFG)
    codebook = yaml.safe_load(open(os.path.join(ROOT, "docs", "codebook.yaml"), encoding="utf-8"))

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "T_VOC.xlsx")
        build_workbook.build_workbook(
            respondents, payments, metrics, codebook,
            template_path=os.path.join(d, "missing_template.xlsx"),
            out_path=out, charts_dir=os.path.join(d, "charts"))
        assert os.path.exists(out)
        wb = load_workbook(out)
        for sheet in ["VOC Collection", "Payments", "Summary", "Codebook", "Method"]:
            assert sheet in wb.sheetnames
        # VOC Collection has header + one row per respondent
        voc = wb["VOC Collection"]
        assert voc.max_row == 1 + len(respondents)
        # Payments has header + one row per payment
        pay = wb["Payments"]
        assert pay.max_row == 1 + len(payments)
