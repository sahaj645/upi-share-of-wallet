"""
analyze.py — compute all metrics from clean data into outputs/metrics.json.

Every number in the deliverables must come from this file's output. No numbers
are hard-coded; they are computed from data/clean only (+ the AISHE constant in
config for sizing). Concept interest is reported SEPARATELY and labelled
"potentially addressable (not a forecast)" — it never enters the sizing GMV.
"""
from __future__ import annotations

import os
import sys
import json

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from ingest import load_config  # noqa: E402

PAYTM = "paytm"


def _is_paytm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().eq(PAYTM)


def _share(mask_paytm: pd.Series, weight: pd.Series | None = None) -> float | None:
    if weight is None:
        n = len(mask_paytm)
        return round(float(mask_paytm.sum()) / n, 4) if n else None
    total = float(weight.sum())
    return round(float(weight[mask_paytm].sum()) / total, 4) if total else None


def paytm_shares(pay: pd.DataFrame) -> dict:
    """Paytm share by count and by value, for all / small / large slices."""
    out = {}
    for label, sub in {
        "all": pay,
        "small": pay[pay["is_small"] == True],   # noqa: E712
        "large": pay[pay["is_small"] == False],  # noqa: E712
    }.items():
        if len(sub) == 0:
            out[label] = {"by_count": None, "by_value": None, "n": 0}
            continue
        is_p = _is_paytm(sub["app"])
        out[label] = {
            "by_count": _share(is_p),
            "by_value": _share(is_p, sub["amount"].fillna(0)),
            "n": int(len(sub)),
        }
    return out


def compute_metrics(respondents: pd.DataFrame, payments: pd.DataFrame, cfg: dict) -> dict:
    m: dict = {"_meta": {
        "note": "All figures computed from observed data only. Concept interest "
                "is potentially addressable, NOT an adoption forecast.",
        "n_respondents": int(len(respondents)),
        "n_voc": int((respondents.get("is_voc") == True).sum()) if "is_voc" in respondents else None,  # noqa: E712
        "n_indepth": int((respondents.get("is_indepth") == True).sum()) if "is_indepth" in respondents else None,  # noqa: E712
        "n_payments": int(len(payments)),
    }}

    # counts per group
    if "group" in respondents:
        m["group_counts"] = respondents["group"].value_counts(dropna=False).rename(
            index=lambda x: "none" if pd.isna(x) else x).to_dict()

    if len(payments):
        payments = payments.copy()
        payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce")

        # overall paytm share
        m["paytm_share"] = paytm_shares(payments)

        # by group
        grp = payments.merge(
            respondents[["voc_id", "group"]], on="voc_id", how="left")
        m["paytm_share_by_group"] = {
            (g if pd.notna(g) else "none"): paytm_shares(sub)
            for g, sub in grp.groupby("group", dropna=False)
        }
        # by occasion (type)
        m["paytm_share_by_occasion"] = {
            str(t): paytm_shares(sub)
            for t, sub in payments.groupby("type", dropna=False)
        }
        # 'why that app' distribution (raw)
        m["why_app_distribution"] = (
            payments["why"].dropna().astype(str).str.strip().str.lower()
            .value_counts().head(20).to_dict())

    # switching (raw signal; coded triggers filled in P5/P6 from final_code)
    if "switch_history" in respondents:
        sw = respondents["switch_history"].dropna().astype(str).str.strip()
        switched = sw[~sw.str.lower().isin(["", "no", "never", "nan"])]
        m["switching"] = {"n_reported_switch": int(len(switched))}

    # funding source
    if "funding" in respondents:
        m["funding_source"] = respondents["funding"].dropna().value_counts().to_dict()
    # parent uses paytm
    if "parent_uses_paytm" in respondents:
        m["parent_uses_paytm"] = respondents["parent_uses_paytm"].dropna().value_counts().to_dict()
    # money reaches (channel)
    if "money_reaches" in respondents:
        m["money_reaches"] = respondents["money_reaches"].dropna().value_counts().to_dict()

    # concept score distribution — reported separately, labelled clearly
    if "concept_score" in respondents:
        cs = pd.to_numeric(respondents["concept_score"], errors="coerce").dropna()
        dist = cs.round().astype(int).value_counts().sort_index().to_dict()
        pct_45 = round(float((cs >= 4).sum()) / len(cs), 4) if len(cs) else None
        m["concept_interest"] = {
            "label": "potentially addressable (not a forecast)",
            "score_distribution": {str(k): int(v) for k, v in dist.items()},
            "pct_rated_4_or_5": pct_45,
            "n_answered": int(len(cs)),
        }

    # opportunity sizing — observed data + AISHE constant only
    m["sizing"] = _sizing(respondents, payments, cfg, m)
    return m


def _sizing(respondents, payments, cfg, m) -> dict:
    aishe = cfg.get("aishe_enrolment")
    sizing = {
        "method": "Observed proportions scaled by AISHE enrolment. Not a forecast; "
                  "concept interest is excluded from this figure.",
        "aishe_enrolment": aishe,
    }
    # non-Paytm value share among captured payments = observed leakage
    if len(payments):
        share_all = m.get("paytm_share", {}).get("all", {})
        pv = share_all.get("by_value")
        if pv is not None:
            sizing["observed_paytm_value_share"] = pv
            sizing["observed_leakage_value_share"] = round(1 - pv, 4)
    # share of respondents who use UPI but are not Paytm-primary (switchable pool)
    if "group" in respondents and len(respondents):
        non_paytm_primary = respondents["group"].isin(["G2", "G3"]).sum()
        base = respondents["is_voc"].eq(True).sum() if "is_voc" in respondents else len(respondents)  # noqa: E712
        if base:
            frac = round(float(non_paytm_primary) / float(base), 4)
            sizing["non_paytm_primary_share_of_voc"] = frac
            if aishe:
                sizing["addressable_users_upper_bound"] = int(round(frac * aishe))
                sizing["addressable_users_note"] = (
                    "Upper bound = non-Paytm-primary UPI users share x AISHE "
                    "enrolment. Observed proportion only; not an adoption estimate.")
    return sizing


def main():
    cfg = load_config()
    paths = cfg["paths"]
    rp = os.path.join(ROOT, paths["clean_respondents"])
    pp = os.path.join(ROOT, paths["clean_payments"])
    if not os.path.exists(rp):
        print(f"NOTE: {rp} not found — run src/ingest.py after DATA PULL first.")
        return
    respondents = pd.read_csv(rp)
    payments = pd.read_csv(pp) if os.path.exists(pp) else pd.DataFrame(
        columns=["voc_id", "n", "amount", "type", "app", "why", "is_small"])
    metrics = compute_metrics(respondents, payments, cfg)
    out = os.path.join(ROOT, paths["metrics"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
