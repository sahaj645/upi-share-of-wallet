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
