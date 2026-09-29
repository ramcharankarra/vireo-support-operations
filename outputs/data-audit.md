# Vireo Audio Support Data Pack (Set D) — Comprehensive Data Audit Report

**Date:** 28 September 2026  
**Subject:** First-Response SLA Data Audit, Data Integrity Validation, and Operational Baseline  
**Scope:** `tickets.csv`, `agents.csv`, `customers.csv`, `orders.csv`, `products.csv`, `support-policy.pdf` (v3.2), `email-thread.txt`

---

## 1. Population & Migration Deduplication

| Metric | Count | Audit Finding & Methodology |
| :--- | :--- | :--- |
| **Raw Ticket Rows** | 11,816 | Raw rows exported from Helpdesk API (`helpdesk`: 8,079; `legacy_fd`: 3,737). |
| **Unique Ticket IDs** | 11,200 | Deduplicated ticket universe. |
| **Duplicated Ticket IDs** | 616 | Exactly 616 IDs appear twice (1,232 rows total). |
| **Duplicate Source Distribution** | 100% Dual | Every single duplicated ticket ID exists in both `helpdesk` and `legacy_fd`. |
| **Deduplication Resolution Rule** | `helpdesk` Priority | When a ticket ID appears in both systems, the current `helpdesk` record is retained, discarding the legacy Freshdesk migration re-import. |
| **Post-Dedup Composition** | 11,200 | 8,079 original `helpdesk` rows + 3,121 non-duplicate `legacy_fd` rows. |

---

## 2. Relational Integrity & Schema Validation

All primary and foreign key references across the 8-file pack were validated against their source tables:

- **Customer References (`customer_id`):** 11,200 of 11,200 tickets (100%) match valid records in `customers.csv`. 0 invalid customer references.
- **Agent References (`agent_id`):** 11,200 of 11,200 tickets (100%) match valid agent IDs in `agents.csv`. 0 invalid agent references.
- **Product References (`product_sku`):** 11,200 of 11,200 tickets (100%) match valid SKUs in `products.csv`. 0 invalid product references.
- **Order References (`order_id`):** 7,360 tickets quote an order ID; 100% of non-blank order IDs match valid records in `orders.csv`. 3,840 tickets are blank (customers seeking pre-sales or general advice without quoting order ID).
- **Team Assignment vs Roster Team:** 945 tickets were resolved by an agent whose roster team differed from the initial intake routing (`assigned_team`), reflecting cross-team escalations and hand-offs.
- **Transfers (`transfers`):** Range from 0 to 2 transfers across tickets (0 transfers: 10,255; 1 transfer: 941; 2 transfers: 4).

---

## 3. Timestamp & Timezone Rules

- **Helpdesk API Timezone:** Timestamps in `tickets.csv` (`created_at`, `first_response_at`, `resolved_at`) are exported in UTC.
- **Operating Policy Timezone:** Support Operating Policy v3.2 specifies shifts and hours in Indian Standard Time (IST, UTC+05:30).
- **Timezone Conversion:** All timestamps are converted to timezone-aware IST representations (`created_at_ist`, `first_response_at_ist`, `resolved_at_ist`).
- **Duration Invariance:** First-response duration `(first_response_at - created_at)` in minutes is identical whether calculated in UTC or IST.
- **Missing Timestamps:**
  - `created_at`: 0 missing.
  - `first_response_at`: 0 missing.
  - `resolved_at`: 589 missing (corresponds to 353 open and 236 pending tickets).
  - Negative response durations: 0 instances.

---

## 4. Historical Roster Matching & June Shift Reshuffle

- **Roster Composition:** `agents.csv` contains 46 assignment rows for 44 distinct agents.
- **Indore Shift Changes:** Agents **A3002** (Tarun Mishra) and **A3003** (Harpreet Deshpande) were assigned to the Night shift from 2023 until 2025-06-29, and reassigned to Day shift starting 2025-06-30.
- **Date Matching Rule:** Tickets are matched to roster assignments using `agent_id` and the ticket's IST creation date:
  $$\text{from\_date} \le \text{ticket\_date} \le \text{to\_date}$$
  Where `to_date` is inclusive for the full calendar day.
- **Roster Match Rate:** 11,200 of 11,200 tickets (100.0%) successfully matched a valid historical assignment. **0 unmatched tickets**.

---

## 5. SLA Engine & Deterministic Baseline

### Policy Rules (Policy v3.2 §3)
- First-response targets: **Chat: 15 min**, **Voice: 120 min (2h)**, **Social: 240 min (4h)**, **Email: 480 min (8h)**.
- **Exact Boundary Condition:** A ticket is in breach strictly when $\text{response\_minutes} > \text{target\_minutes}$. Exactly at target ($\le$) is **not** a breach. (55 tickets in the dataset sit exactly at the threshold and are correctly classified as compliant).
- **Store Credit:** Every SLA breach produces a ₹350 store-credit exposure.

### Verified Baseline Summary

| Dimension | Category | Ticket Volume | SLA Breaches | Breach Rate | SLA Credit Exposure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total** | **All Tickets** | **11,200** | **2,440** | **21.79%** | **₹854,000** |
| **Channel** | Chat | 4,959 | 1,368 | 27.59% | ₹478,800 |
| | Email | 3,647 | 745 | 20.43% | ₹260,750 |
| | Social | 1,106 | 243 | 21.97% | ₹85,050 |
| | Voice | 1,488 | 84 | 5.65% | ₹29,400 |
| **Shift** | Morning (06:00–14:00) | 6,264 | 2,018 | 32.22% | ₹706,300 |
| | Day (14:00–22:00) | 4,668 | 393 | 8.42% | ₹137,550 |
| | Night (22:00–06:00) | 268 | 29 | 10.82% | ₹10,150 |

---

## 6. Data Quality Signals & Special Investigations

### A. Customer Satisfaction (CSAT) Normalization (Policy §8)
- In the legacy tool, score `0` was recorded when a customer did not respond.
- Raw tickets contain 2,066 zero scores; deduplicated tickets contain 1,730 zero scores.
- In `csat_clean`, all `0` scores are converted to `NaN`.
- Resulting survey responses: 4,993 valid ratings (1 to 5), representing a 44.58% response rate, exactly matching policy expectation (~45%). Mean CSAT is 3.37.

### B. Policy §5 Violation: Simultaneous Refund and Replacement
- Operating Policy §5 explicitly states: *"In no case is a customer to receive both a refund and a replacement for the same order; where this happens in error it must be escalated to the Team Lead and Finance the same day."*
- **Audit Finding:** Exactly **6 tickets** contain both a positive refund amount and `replacement_issued == 'Y'`:
  - `TK-240173`: ₹3,499 refund + replacement
  - `TK-240212`: ₹3,499 refund + replacement
  - `TK-240398`: ₹3,499 refund + replacement
  - `TK-240401`: ₹3,499 refund + replacement
  - `TK-240498`: ₹3,499 refund + replacement
  - `TK-240578`: ₹3,499 refund + replacement
- These are surfaced as audit exceptions for finance and team lead review.

### C. Voice Transcripts & IVR Failure Investigation
- Sameer's email noted: *"About forty messages are failed IVR transcripts."*
- Total Voice tickets: 1,488.
- Voice tickets tagged with `[IVR transcript]`: 902 (916 across all channels).
- Audio defect bracketed tags: 14 tickets contain `[inaudible]` (12), `[crosstalk]` (4), or `[line dropped]` (2).
- Failure/error wording in IVR messages: **44 tickets** contain failure/interruption terms (`failed`, `dropped`, `inaudible`, `disconnect`), closely validating Sameer's count of "about forty".

### D. Finance & Leadership Claims Check (Arjun vs Priya)
- **Arjun's statement:** *"SLA credit line in the P&L has roughly tripled since last summer."*
  - **Audit observation:** In early 2025 (Jan–Jun 2025), monthly SLA credits were ₹7,350 to ₹14,350. By August 2025, credits rose to ₹65,800/month, and stabilized at ₹63,000–₹74,550/month in 2026 (~5x early 2025 levels).
  - **Limitation statement:** *"Available ticket data does not establish the historical P&L comparison"* for summer 2024 because the ticket export begins on 1 January 2025.
- **Priya's statement:** *"Credits look flat to me month on month."*
  - **Audit observation:** Confirmed for recent operations. Between October 2025 and June 2026, monthly credits fluctuated within a tight corridor (₹63,350 to ₹74,550), appearing virtually flat month-on-month.

---

## 7. Weekly Boundaries & Partial Weeks

- Weekly reporting aggregates from Monday to Sunday in IST.
- The dataset boundaries span 1 January 2025 (Wednesday) to 30 June 2026 (Tuesday).
- Two partial weeks are explicitly identified:
  1. **Week 2024-12-30:** 5 days (Jan 1 to Jan 5, 2025) — 31 tickets, 0 breaches.
  2. **Week 2026-06-29:** 2 days (Jun 29 to Jun 30, 2026) — 31 tickets, 3 breaches.
- Both are explicitly flagged as `partial_week` to prevent misleading week-on-week comparisons.

