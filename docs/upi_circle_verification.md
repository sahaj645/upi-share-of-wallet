# UPI Circle verification log

**Rule (A8):** In the PDF, say "Paytm supports X" only for rows marked
**VERIFIED** here. Anything NOT_FOUND or DIFFERENT is written as a proposal
("we propose Paytm add…"), never as an existing feature.

Sahaj fills the **Status**, **Observed value**, and **Evidence** columns from the
Paytm app and puts blurred screenshots in `docs/evidence/`. Leave blank until
verified in-app.

Status values: `VERIFIED` / `NOT_FOUND` / `DIFFERENT`

| # | Claim to check (from sources) | Status | Observed value in app | Evidence file |
|---|-------------------------------|--------|-----------------------|---------------|
| 1 | Paytm lets a primary user add a **secondary user** in UPI Circle | | | |
| 2 | Under NPCI rules, **full delegation** is capped at **₹5,000 per payment** | | | |
| 3 | Full delegation is capped at **₹15,000 per month** | | | |
| 4 | A primary user can add up to **5 secondary users** | | | |
| 5 | A secondary user **does not need their own bank account** | | | |
| 6 | (Other UPI Circle capability relevant to the chosen solution) | | | |

**Sources (to be confirmed in-app, not quoted as fact until VERIFIED):**
- Paytm Blog — UPI Circle transaction limits
- Paytm FAQ — How to add a secondary user in UPI
- NPCI — UPI delegation / UPI Circle guidelines

_Last verified in-app: ____________ (date, app version)_
