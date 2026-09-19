# CLAUDE.md — Paytm UPI Challenge (non-negotiable rules)

1. NEVER fabricate, simulate or "fill in" survey responses, quotes, or interview notes.
   Synthetic data is allowed ONLY in `tests/fixtures/` and must be marked SYNTHETIC.
   It must never reach `deliverables/`.
2. `data/raw/` is gitignored. Never commit raw exports, names, phone numbers,
   emails, UPI IDs or un-blurred screenshots.
3. Every number in the PDF and the Summary sheet must come from `outputs/metrics.json`.
   No hard-coded or example numbers in deliverables.
4. Barrier codes proposed by Claude go to `suggested_code`. Only `final_code`
   (filled in by Sahaj) is used in the analysis.
5. Don't claim any Paytm feature exists unless `docs/upi_circle_verification.md`
   marks it VERIFIED.
6. Commit at every checkpoint with conventional commit messages, then push to `origin main`.
7. The exec summary PDF must be exactly 2 pages. `validate.py` enforces this.

## Division of labour

**Claude Code builds:** the Google Form (Apps Script), the data pipeline, the
analysis, the charts, the VOC workbook and the 2-page PDF. It commits and pushes
at every checkpoint.

**Only Sahaj can:** run the form, hold the interviews, verify UPI Circle in the
app, confirm barrier codes, and choose the final solution.

## Standing instruction (every session)

After each phase, run the tests and `git status`, confirm nothing in `data/raw`
is staged, commit with the listed message and push. If the human check for that
phase is not complete, stop and ask.

## What's left (status as of 19 Sep 2026)

**DONE (built, tested, pushed):** whole software pipeline — scaffold, survey
instruments, form generator, ingest/analyze/charts/coding/workbook/summary/
validate, tests (22 passing), CI, `run_pipeline.py`. Team name set to
**Aquaholics**. Official brief + VOC template in `reference/`; workbook fills the
real template. Nothing more to code.

**LEFT — human only (Sahaj). Claude cannot do these without fabricating data:**

1. **Collect 50 VOCs** (≥10 in-depth), Track A segment = used Paytm in last 90d
   but another app is primary. Launch `survey/create_form.gs`; run interviews
   using `survey/interview_guide.md`; save interview notes from
   `survey/interview_template.md` into `data/raw/interviews/` (gitignored).
2. **Download responses** CSV → `data/raw/form_responses.csv`.
3. **Verify UPI Circle in the Paytm app** → fill `docs/upi_circle_verification.md`
   (Status = VERIFIED/NOT_FOUND/DIFFERENT); put blurred screenshots in
   `docs/evidence/`. Only VERIFIED items may be stated as existing features.
4. **Confirm barrier codes** → fill `final_code` in `data/clean/coding_sheet.csv`
   (add new codes to `docs/codebook.yaml` if a theme appears 3+ times).
5. **Confirm the solution** in `docs/decision.md` (apply the A7 rule; sign the
   confirmation block).
6. **Pick 3 real quotes** into the "Selected" list of `docs/quote_shortlist.md`.
7. **Export the PDF** if `docx2pdf`/Word is unavailable: open
   `deliverables/Aquaholics_ExecSummary.docx` in Word → Save as PDF (B6).

**Then, to produce the deliverables:**

```
python run_pipeline.py     # ingest → code_barriers → analyze → charts →
                           # build_workbook → build_summary → validate
```

Fix any `validate.py` failures, then `git tag v1.0-submission && git push --tags`.
Submit `deliverables/Aquaholics_VOC.xlsx` + `Aquaholics_ExecSummary.pdf` by 20:00
IST, 20 Sep 2026.
