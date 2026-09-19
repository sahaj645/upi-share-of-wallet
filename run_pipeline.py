"""
run_pipeline.py — one command to run the whole pipeline.

Real mode (after DATA PULL — data lands in data/raw/):
    python run_pipeline.py
  Runs, in order: ingest -> code_barriers -> analyze -> charts ->
  build_workbook -> build_summary -> validate. Each step guards itself if
  its inputs are missing, so it is safe to run early.

Demo mode (proves the chain works on SYNTHETIC fixtures):
    python run_pipeline.py --demo
  Builds clean tables, metrics, charts, a VOC workbook and an exec-summary
  docx from tests/fixtures INTO a throwaway ./demo/ folder. Nothing synthetic
  is ever written to deliverables/ or committed.

Guardrail: --demo output is clearly SYNTHETIC and lives only in ./demo/.
"""
from __future__ import annotations

import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

STEPS = [
    "ingest.py",
    "code_barriers.py",
    "analyze.py",
    "charts.py",
    "build_workbook.py",
    "build_summary.py",
    "validate.py",
]


def run_real() -> int:
    for step in STEPS:
        print(f"\n=== {step} ===")
        rc = subprocess.call([sys.executable, os.path.join(SRC, step)],
                             env={**os.environ, "PYTHONUTF8": "1"})
        # validate.py returns 1 as a gate result; report but don't crash the run
        if rc != 0 and step != "validate.py":
            print(f"[stop] {step} exited {rc}")
            return rc
    return 0


def run_demo() -> int:
    import pandas as pd
    import yaml
    sys.path.insert(0, SRC)
    import ingest, analyze, charts, build_workbook, build_summary  # noqa: E401

    fix = os.path.join(HERE, "tests", "fixtures")
    demo = os.path.join(HERE, "demo")
    os.makedirs(os.path.join(demo, "charts"), exist_ok=True)
    cfg = ingest.load_config()

    df = pd.read_csv(os.path.join(fix, "form_responses.SYNTHETIC.csv"))
    fr, fp = ingest.build_from_form(df, 500)
    ir, ip = ingest.build_from_interviews(os.path.join(fix, "interviews"), 500)
    respondents = pd.concat([fr, ir], ignore_index=True)
    payments = pd.concat([fp, ip], ignore_index=True)
    respondents.to_csv(os.path.join(demo, "respondents.SYNTHETIC.csv"), index=False)
    payments.to_csv(os.path.join(demo, "payments.SYNTHETIC.csv"), index=False)

    metrics = analyze.compute_metrics(respondents, payments, cfg)
    with open(os.path.join(demo, "metrics.SYNTHETIC.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)

    charts.render_all(metrics, os.path.join(demo, "charts"),
                      os.path.join(demo, "no_coding.csv"))

    codebook = yaml.safe_load(open(os.path.join(HERE, "docs", "codebook.yaml"), encoding="utf-8"))
    build_workbook.build_workbook(
        respondents, payments, metrics, codebook,
        template_path=os.path.join(HERE, cfg["paths"]["voc_template"]),
        out_path=os.path.join(demo, "DEMO_SYNTHETIC_VOC.xlsx"),
        charts_dir=os.path.join(demo, "charts"))
    build_summary.build_summary(
        metrics, verification_path=os.path.join(HERE, "docs", "upi_circle_verification.md"),
        quotes_path=os.path.join(HERE, "docs", "quote_shortlist.md"),
        charts_dir=os.path.join(demo, "charts"),
        out_docx=os.path.join(demo, "DEMO_SYNTHETIC_ExecSummary.docx"), team="DEMO")

    print("\nDemo build complete (SYNTHETIC — not for submission). See ./demo/")
    print(f"  respondents: {len(respondents)}  payments: {len(payments)}")
    print(f"  paytm share (value, all): {metrics['paytm_share']['all']['by_value']}")
    return 0


def main():
    if "--demo" in sys.argv:
        return run_demo()
    return run_real()


if __name__ == "__main__":
    sys.exit(main())
