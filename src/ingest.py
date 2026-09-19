"""
ingest.py — read raw form + interview data, anonymise, reshape.

Inputs (gitignored):
  data/raw/form_responses.csv        Google Sheets export of the form
  data/raw/interviews/*.md           one file per in-depth interview (front-matter)

Outputs (committed, anonymised):
  data/clean/respondents.csv         one row per respondent
  data/clean/payments.csv            one row per payment (long format)

Rules:
  - Drop PII columns (name / phone / email / UPI ID) — never written out.
  - Assign VOC IDs. Derive group G1/G2/G3. Non-installed kept for rates
    (is_voc = False).
  - Reshape the 10 payment blocks into long form with is_small flag.
  - No fabrication: this only transforms whatever is in data/raw.

Importable helpers are used by tests on SYNTHETIC fixtures.
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import yaml
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Match PII-bearing HEADERS/columns only (not incidental words like "your phone").
PII_PATTERNS = re.compile(
    r"(email\s*address|e-?mail|\bphone\s*(number|no\b|#)|\bmobile\s*(number|no\b)"
    r"|whatsapp|contact\s*(number|no\b)|\bupi\s*id\b|\bvpa\b|full\s*name|your\s*name)",
    re.I,
)


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #
def load_config(path: str | None = None) -> dict:
    path = path or os.path.join(ROOT, "config.yaml")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# column matching (Google exports the full question text as headers)
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def find_col(df: pd.DataFrame, *keywords: str) -> str | None:
    """Return the first column whose header contains ALL keywords."""
    kws = [k.lower() for k in keywords]
    for col in df.columns:
        c = _norm(col)
        if all(k in c for k in kws):
            return col
    return None


def coalesce(row: pd.Series, *cols: str | None):
    for c in cols:
        if c and c in row and pd.notna(row[c]) and str(row[c]).strip():
            return row[c]
    return None


# --------------------------------------------------------------------------- #
# group assignment
# --------------------------------------------------------------------------- #
def assign_group(primary_app, paytm_90d, installed) -> str | None:
    """G1/G2/G3 per A3. Returns None for rates-only (not installed)."""
    if not _truthy(installed):
        return None
    if _is_paytm(primary_app):
        return "G1"
    return "G2" if _truthy(paytm_90d) else "G3"


def _is_paytm(v) -> bool:
    return v is not None and "paytm" in str(v).strip().lower()


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"yes", "y", "true", "1"}


# --------------------------------------------------------------------------- #
# respondents + payments from the form export
# --------------------------------------------------------------------------- #
def build_from_form(df: pd.DataFrame, small_max: int, start_idx: int = 1):
    # drop PII columns entirely
    df = df[[c for c in df.columns if not PII_PATTERNS.search(_norm(c))]].copy()

    c_student   = find_col(df, "college student")
    c_upi30     = find_col(df, "upi payment", "30 days")
    c_installed = find_col(df, "paytm installed")
    c_paytm90   = find_col(df, "paytm", "90 days")
    # primary-app appears twice (short + full path); coalesce both
    prim_cols = [c for c in df.columns if "most" in _norm(c) and "upi" in _norm(c)]

    respondents, payments = [], []
    for i, (_, row) in enumerate(df.iterrows()):
        vid = f"V{start_idx + i:03d}"
        primary = coalesce(row, *prim_cols)
        installed = row.get(c_installed) if c_installed else None
        paytm90 = row.get(c_paytm90) if c_paytm90 else None
        group = assign_group(primary, paytm90, installed)
        is_voc = _truthy(installed)  # completed full VOC path

        respondents.append({
            "voc_id": vid,
            "source": "form",
            "is_voc": is_voc,
            "is_indepth": False,
            "group": group,
            "primary_app": primary,
            "paytm_90d": paytm90,
            "paytm_installed": installed,
            "is_student": row.get(c_student) if c_student else None,
            "upi_30d": row.get(c_upi30) if c_upi30 else None,
            "year": _ctx(row, "year of study"),
            "hostel_day": _ctx(row, "hostel or day"),
            "home_state": _ctx(row, "home state"),
            "college": _ctx(row, "college"),
            "funding": _ctx(row, "monthly spending", "funded"),
            "money_reaches": _ctx(row, "money from parents reach"),
            "parent_uses_paytm": _ctx(row, "parent use paytm"),
            "concept_score": _num(_ctx(row, "would you use it")),
            "visibility_pref": _ctx(row, "prefer your parent to see"),
            "who_agrees": _ctx(row, "need to agree"),
            "unprompted_barrier": _ctx(row, "single biggest reason"),
            "last_used_paytm": _ctx(row, "last use paytm"),
            "switch_history": _ctx(row, "switched your primary"),
        })
        payments.extend(_reshape_payments(row, vid, small_max))
    return pd.DataFrame(respondents), pd.DataFrame(payments)


def _ctx(row: pd.Series, *keywords: str):
    col = find_col_series(row, *keywords)
    return row[col] if col else None


def find_col_series(row: pd.Series, *keywords: str) -> str | None:
    kws = [k.lower() for k in keywords]
    for col in row.index:
        c = _norm(col)
        if all(k in c for k in kws):
            return col
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _reshape_payments(row: pd.Series, vid: str, small_max: int):
    out = []
    for n in range(1, 11):
        amt = find_col_series(row, f"payment {n}", "amount")
        typ = find_col_series(row, f"payment {n}", "type")
        app = find_col_series(row, f"payment {n}", "app used")
        why = find_col_series(row, f"payment {n}", "why")
        amount = _num(row[amt]) if amt else None
        if amount is None and not (app and str(row.get(app, "")).strip()):
            continue  # empty payment slot
        out.append({
            "voc_id": vid,
            "n": n,
            "amount": amount,
            "type": row[typ] if typ else None,
            "app": row[app] if app else None,
            "why": row[why] if why else None,
            "is_small": (amount is not None and amount <= small_max),
        })
    return out


# --------------------------------------------------------------------------- #
# interviews (front-matter markdown)
# --------------------------------------------------------------------------- #
def parse_interview(path: str, small_max: int) -> tuple[dict, list[dict]]:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    # strip a leading HTML comment / blank lines before the front-matter block
    text = re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.S)
    text = text.lstrip("﻿ \t\r\n")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    meta = yaml.safe_load(m.group(1)) if m else {}
    meta = meta or {}
    vid = str(meta.get("voc_id") or os.path.splitext(os.path.basename(path))[0])
    group = meta.get("group") or assign_group(
        meta.get("primary_app"), meta.get("paytm_90d"), meta.get("paytm_installed", "yes")
    )
    resp = {
        "voc_id": vid, "source": "interview", "is_voc": True, "is_indepth": True,
        "group": group, "primary_app": meta.get("primary_app"),
        "paytm_90d": meta.get("paytm_90d"), "paytm_installed": meta.get("paytm_installed"),
        "year": meta.get("year"), "hostel_day": meta.get("hostel_day"),
        "home_state": meta.get("home_state"), "college": meta.get("college"),
        "funding": meta.get("funding"), "money_reaches": meta.get("money_reaches"),
        "parent_uses_paytm": meta.get("parent_uses_paytm"),
        "concept_score": _num(meta.get("concept_score")),
        "visibility_pref": meta.get("visibility_pref"), "who_agrees": meta.get("who_agrees"),
        "unprompted_barrier": meta.get("unprompted_barrier"),
        "last_used_paytm": meta.get("last_used_paytm"),
        "switch_history": meta.get("switch_history"),
    }
    payments = []
    for i, p in enumerate(meta.get("payments", []) or [], start=1):
        amount = _num(p.get("amount"))
        payments.append({
            "voc_id": vid, "n": i, "amount": amount,
            "type": p.get("type"), "app": p.get("app"), "why": p.get("why"),
            "is_small": (amount is not None and amount <= small_max),
        })
    return resp, payments


def build_from_interviews(folder: str, small_max: int):
    resp_rows, pay_rows = [], []
    for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
        if os.path.basename(path).lower() == "readme.md":
            continue
        r, ps = parse_interview(path, small_max)
        resp_rows.append(r)
        pay_rows.extend(ps)
    return pd.DataFrame(resp_rows), pd.DataFrame(pay_rows)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    cfg = load_config()
    small_max = int(cfg.get("small_ticket_max", 500))
    paths = cfg["paths"]
    raw_form = os.path.join(ROOT, paths["raw_form"])
    raw_int = os.path.join(ROOT, paths["raw_interviews"])

    resp_frames, pay_frames = [], []
    if os.path.exists(raw_form):
        df = pd.read_csv(raw_form)
        r, p = build_from_form(df, small_max)
        resp_frames.append(r); pay_frames.append(p)
        print(f"form: {len(r)} respondents, {len(p)} payments")
    else:
        print(f"NOTE: {raw_form} not found — run after DATA PULL. Skipping form.")

    if os.path.isdir(raw_int):
        r, p = build_from_interviews(raw_int, small_max)
        if len(r):
            resp_frames.append(r); pay_frames.append(p)
            print(f"interviews: {len(r)} respondents, {len(p)} payments")

    if not resp_frames:
        print("No raw data yet. Nothing written.")
        return

    respondents = pd.concat(resp_frames, ignore_index=True)
    payments = pd.concat(pay_frames, ignore_index=True) if any(len(x) for x in pay_frames) \
        else pd.DataFrame(columns=["voc_id", "n", "amount", "type", "app", "why", "is_small"])

    out_resp = os.path.join(ROOT, paths["clean_respondents"])
    out_pay = os.path.join(ROOT, paths["clean_payments"])
    os.makedirs(os.path.dirname(out_resp), exist_ok=True)
    # final PII guard on output
    respondents = respondents[[c for c in respondents.columns if not PII_PATTERNS.search(c)]]
    respondents.to_csv(out_resp, index=False, encoding="utf-8")
    payments.to_csv(out_pay, index=False, encoding="utf-8")
    print(f"wrote {out_resp} ({len(respondents)} rows)")
    print(f"wrote {out_pay} ({len(payments)} rows)")


if __name__ == "__main__":
    sys.exit(main())
