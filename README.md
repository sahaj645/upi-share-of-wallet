# Paytm UPI Growth Challenge — Round 1 (Track A)

Research and proposal pipeline for building **primary-app preference** among
college students. The spec is
[`reference/Paytm_Round1_Plan_v2.docx`](reference/Paytm_Round1_Plan_v2.docx);
the non-negotiable rules live in [`CLAUDE.md`](CLAUDE.md).

## What this repo produces

- A neutral survey (Google Form via Apps Script) + in-depth interview guide
- An anonymising ingestion pipeline (form + interviews → clean tables)
- Analysis of Paytm share of wallet, barriers, switching triggers, and
  observed-data opportunity sizing
- Two deliverables: `TeamName_VOC.xlsx` and a 2-page `TeamName_ExecSummary.pdf`

Every number in the deliverables comes from `outputs/metrics.json`. No data is
ever fabricated — synthetic rows exist only in `tests/fixtures/` and are marked
SYNTHETIC.

## Setup

```bash
python --version   # 3.11+
pip install -r requirements.txt
```

## Run the whole pipeline (one command)

```bash
python run_pipeline.py
```

Runs, in order: ingest → code_barriers → analyze → charts → build_workbook →
build_summary → validate. Each step guards itself if its inputs are missing, so
it is safe to run before data has landed.

See the chain work on synthetic fixtures (writes to a throwaway `./demo/`, never
to `deliverables/`):

```bash
python run_pipeline.py --demo
```

## Or run each step by hand

```bash
python src/ingest.py         # data/raw → data/clean (anonymised)
python src/code_barriers.py  # build coding sheet (suggested codes only)
python src/analyze.py        # data/clean → outputs/metrics.json
python src/charts.py         # outputs/metrics.json → outputs/charts/*.png
python src/build_workbook.py # → deliverables/TeamName_VOC.xlsx
python src/build_summary.py  # → deliverables/TeamName_ExecSummary.pdf
python src/validate.py       # gate before submission
```

Run the tests (synthetic fixtures only):

```bash
pytest
```

## Repository layout

```
├─ CLAUDE.md  README.md  config.yaml  .gitignore
├─ reference/            brief PDF, VOC template, this plan
├─ survey/               questionnaire.md, interview_guide.md, consent.md, create_form.gs
├─ docs/                 codebook.yaml, upi_circle_verification.md, decision.md, evidence/ (blurred)
├─ data/raw/             (gitignored) form_responses.csv, interviews/*.md
├─ data/clean/           respondents.csv, payments.csv, coding_sheet.csv (anonymised)
├─ src/                  ingest.py, code_barriers.py, analyze.py, charts.py,
│                        build_workbook.py, build_summary.py, validate.py
├─ tests/                fixtures/ (SYNTHETIC), test_*.py
├─ outputs/              metrics.json, charts/*.png
└─ deliverables/         TeamName_VOC.xlsx, TeamName_ExecSummary.pdf
```

## Human checkpoints (only Sahaj)

Run the form, hold the interviews, verify UPI Circle in the app, confirm every
barrier `final_code`, and choose the final solution. See the phase runbook in
the plan document.
