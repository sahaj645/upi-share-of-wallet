"""
code_barriers.py — build the barrier coding sheet.

Reads clean respondents, reads each open answer against docs/codebook.yaml, and
proposes a primary + secondary code with a rationale. Writes
data/clean/coding_sheet.csv with `final_code` LEFT BLANK.

Guardrail #4: only `final_code` (filled by Sahaj) is used in analysis. Claude's
suggestions live in `suggested_code` / `suggested_secondary`.

It also lists any theme appearing in 3+ answers that no current code covers, so
Sahaj can add a code before confirming.
"""
from __future__ import annotations

import os
import re
import sys
import csv
from collections import Counter

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from ingest import load_config  # noqa: E402

# keyword triggers per codebook id (kept in sync with docs/codebook.yaml)
KEYWORDS: dict[str, list[str]] = {
    "habit_default":        ["habit", "default", "used to", "always", "first", "auto"],
    "merchant_qr":          ["qr", "merchant", "shop", "scan", "soundbox", "store", "accept"],
    "peer_network":         ["friend", "friends", "split", "peer", "everyone", "roommate", "group"],
    "rewards_cashback":     ["cashback", "reward", "offer", "scratch", "points", "discount", "coupon"],
    "reliability_failures": ["fail", "failed", "error", "decline", "delay", "stuck", "not working", "server"],
    "ui_ease":              ["easy", "fast", "simple", "ui", "interface", "quick", "smooth", "convenient"],
    "trust_safety":         ["trust", "safe", "security", "secure", "fraud", "scam", "privacy"],
    "onboarding_kyc":       ["kyc", "setup", "verify", "link", "bank", "wallet", "register", "account"],
    "not_installed":        ["not installed", "uninstall", "storage", "space", "deleted", "don't have", "dont have"],
}
STOP = set("the a an and or to of for i my me you it is are was use uses used using "
           "app apps paytm phonepe gpay bhim upi pay payment payments because so "
           "with on in at that this instead more most just only very not no yes".split())


def match_codes(text: str) -> tuple[str, str, str]:
    """Return (primary, secondary, rationale) for one open answer."""
    t = (text or "").lower()
    hits = []
    for code, kws in KEYWORDS.items():
        matched = [k for k in kws if k in t]
        if matched:
            hits.append((len(matched), code, matched))
    if not hits:
        return ("no_reason_given" if t.strip() else "", "", "no keyword match")
    hits.sort(reverse=True)
    primary = hits[0][1]
    secondary = hits[1][1] if len(hits) > 1 else ""
    rationale = "; ".join(f"{c}:{'/'.join(mk)}" for _, c, mk in hits[:2])
    return (primary, secondary, rationale)


def uncovered_themes(texts: list[str], min_count: int = 3) -> list[tuple[str, int]]:
    covered = {w for kws in KEYWORDS.values() for k in kws for w in k.split()}
    counter: Counter = Counter()
    for t in texts:
        for w in re.findall(r"[a-z']+", (t or "").lower()):
            if len(w) >= 3 and w not in STOP and w not in covered:
                counter[w] += 1
    return [(w, c) for w, c in counter.most_common() if c >= min_count]


def build_coding_sheet(respondents: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in respondents.iterrows():
        if "is_voc" in r and r.get("is_voc") not in (True, "True", 1):
            continue  # code VOCs only
        barrier = str(r.get("unprompted_barrier") or "").strip()
        switch = str(r.get("switch_history") or "").strip()
        primary, secondary, rationale = match_codes(barrier + " " + switch)
        rows.append({
            "voc_id": r.get("voc_id"),
            "group": r.get("group"),
            "unprompted_answer": barrier,
            "switch_answer": switch,
            "suggested_code": primary,
            "suggested_secondary": secondary,
            "rationale": rationale,
            "final_code": "",          # Sahaj fills this
            "final_secondary": "",
        })
    return pd.DataFrame(rows)


def main():
    cfg = load_config()
    paths = cfg["paths"]
    rp = os.path.join(ROOT, paths["clean_respondents"])
    if not os.path.exists(rp):
        print(f"NOTE: {rp} not found — run src/ingest.py after DATA PULL first.")
        return
    respondents = pd.read_csv(rp)
    sheet = build_coding_sheet(respondents)
    out = os.path.join(ROOT, paths["coding_sheet"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL, encoding="utf-8")
    print(f"wrote {out} ({len(sheet)} rows to confirm)")

    themes = uncovered_themes(sheet["unprompted_answer"].tolist())
    if themes:
        print("\nThemes appearing 3+ times with NO current code (consider adding):")
        for w, c in themes:
            print(f"  {w}: {c}")
    print("\nACTION FOR SAHAJ: review every row, fill final_code, add codes if needed.")


if __name__ == "__main__":
    sys.exit(main())
