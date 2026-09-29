# Vireo Audio — Support Tickets (Set D)
## Final Assessment Submission Form

---

### 1. Deliverable Information
- **Project Name:** Vireo Audio — Support SLA Control Room
- **Primary Business Output:** Weekly First-Response SLA Breach Report by Resolving Agent and Shift
- **Repository Artifacts:**
  - Application: `app.py`
  - Analytics & SLA Engine: `vireo/analysis.py`
  - Automated Test Suite: `tests/test_analysis.py` (14 automated tests)
  - Data Audit: `outputs/data-audit.md`
  - Executive Memo: `outputs/memo.md`
  - Demo Script: `outputs/demo-script.md`
  - Dependencies: `requirements.txt`
  - Setup Guide: `README.md`

---

### 2. Business Goal & Context
To provide Vireo Audio operations leadership (Neha Kulkarni) with a deterministic, auditable weekly first-response SLA breach report by agent and shift, quantifying financial exposure at ₹350 store credit per breach, while addressing stakeholder concerns across Finance (Arjun Mehta) and Customer Experience (Priya Raman).

---

### 3. Core Verified Baseline
Following migration deduplication, the verified baseline across the full ticket universe (1 Jan 2025 – 30 Jun 2026) is:
- **Total Population:** 11,200 unique tickets
- **Total SLA Breaches:** 2,440 tickets
- **Overall Breach Rate:** 21.79%
- **Total SLA-Credit Exposure:** ₹854,000 (at ₹350/breach)
- **By Shift:**
  - **Morning (06:00–14:00 IST):** 6,264 tickets | 2,018 breaches | 32.22% breach rate | ₹706,300 credit exposure (82.7% of all breaches)
  - **Day (14:00–22:00 IST):** 4,668 tickets | 393 breaches | 8.42% breach rate | ₹137,550 credit exposure
  - **Night (22:00–06:00 IST):** 268 tickets | 29 breaches | 10.82% breach rate | ₹10,150 credit exposure
- **By Channel:**
  - **Chat (15 min SLA):** 4,959 tickets | 1,368 breaches | 27.59% breach rate | ₹478,800 exposure
  - **Email (8 hr SLA):** 3,647 tickets | 745 breaches | 20.43% breach rate | ₹260,750 exposure
  - **Social (4 hr SLA):** 1,106 tickets | 243 breaches | 21.97% breach rate | ₹85,050 exposure
  - **Voice (2 hr SLA):** 1,488 tickets | 84 breaches | 5.65% breach rate | ₹29,400 exposure

---

### 4. Technical Architecture & Technology Stack
- **Languages & Frameworks:** Python 3, Pandas, Streamlit, Plotly Express, Pytest.
- **Design Philosophy:** 100% deterministic calculations in core Python. No LLMs in the critical path.
- **Architectural Exclusions:** Deliberately discarded React, Next.js, external databases, LangChain, RAG, and ML prediction to maintain zero-infrastructure simplicity, auditability, and speed.
- **AI Integration:** Controlled explanation layer using OpenAI (optional). The LLM receives pre-aggregated, verified metrics only and is strictly prohibited from recalculating data or recommending hiring. Graceful deterministic fallback ensures full functionality without an API key.

---

### 5. Policy Rules & Scope Decisions
1. **Migration Deduplication:** 616 ticket IDs appeared twice due to Freshdesk migration re-imports. All 616 pairs were verified to contain one `helpdesk` and one `legacy_fd` record; the current `helpdesk` record is prioritized and retained.
2. **Timezone Standardization:** Timestamps in raw exports are UTC. They are converted to `Asia/Kolkata` (IST) before calculating calendar dates, shift assignments, and weekly aggregations. Response elapsed durations are mathematically invariant under timezone conversion.
3. **Historical Roster Matching:** 46 roster assignment rows cover 44 agents. Roster matches use `agent_id` and ticket creation date in IST ($\text{from\_date} \le \text{date} \le \text{to\_date}$, inclusive). The June 2025 Indore reshuffle (agents A3002 and A3003 moving from Night to Day on 2025-06-30) is accurately respected. Unmatched roster tickets: 0.
4. **Exact SLA Boundary Behavior:** In accordance with Policy §3, a breach occurs strictly when $\text{response\_minutes} > \text{target\_minutes}$. Exactly at target ($\le$) is non-breaching (55 tickets in dataset).
5. **Tier 2 Separation:** Per Policy §6, Tier 2 (Escalations & Warranty) cases are multi-touch and measured in days, not weekly volume. Tier 2 agents are strictly separated in reporting to prevent misleading comparisons with Tier 1 frontline agents.
6. **CSAT Normalization:** Legacy Freshdesk recorded `0` for unreturned surveys. 1,730 zero ratings were converted to `NaN`, yielding 4,993 valid responses (mean 3.37, 44.58% response rate, aligning with Policy §8's ~45% expectation).
7. **Policy §5 Violation Surfacing:** Identified exactly 6 orders where customers received both a monetary refund and a replacement unit—flagged for immediate finance recovery.
8. **IVR Investigation:** Identified 44 voice transcript tickets containing failure/dropped wording, validating IT's estimate of "about forty failed IVR transcripts."

---

### 6. Automated Validation & Quality Assurance
The test suite in `tests/test_analysis.py` contains 14 automated tests executing in under 1 second:
1. `test_migration_deduplication`: Validates 11,816 raw rows, 11,200 unique IDs, 616 duplicates, and 100% helpdesk retention.
2. `test_sla_thresholds`: Validates policy targets (chat 15m, voice 120m, social 240m, email 480m) and ₹350 credit.
3. `test_exact_boundary_behavior`: Validates strict inequality ($>$ vs $\ge$) on synthetic cases and confirms all 55 exact boundary tickets in the dataset are non-breaches.
4. `test_utc_to_ist_conversion`: Validates `Asia/Kolkata` timezone attachment, UTC+05:30 offset, and duration invariance.
5. `test_roster_date_matching_and_june_changes`: Validates 100% roster match rate and historical shift transitions for A3002 and A3003 before and after 2025-06-30.
6. `test_csat_normalization`: Validates removal of 1,730 zeros and retention of valid 1–5 scores.
7. `test_weekly_grouping_and_partial_weeks`: Validates Monday-to-Sunday IST cycles and boundary partial weeks (2024-12-30 and 2026-06-29).
8. `test_credit_calculation_and_baseline`: Validates 2,440 breaches, 21.79% breach rate, and ₹854,000 credit total.
9. `test_channel_baseline`: Validates exact channel volumes and breach counts.
10. `test_shift_baseline`: Validates exact shift volumes and breach counts.
11. `test_agent_report_structure`: Validates 46 agent-shift rows, neutral ordering, and Tier 2 separation.
12. `test_refund_replacement_policy_exception`: Validates detection of the 6 Policy §5 exceptions.
13. `test_ivr_investigation_metrics`: Validates voice tickets (1,488), IVR transcripts (902), and failure wording (44).
14. `test_monthly_report_finance`: Validates 18 monthly buckets and credit trends.

---

### 7. Recommendations & Operational Guidance
1. **Zero-Headcount Mandate:** Headcount is frozen through Q4 per Arjun (Finance). Hiring is strictly excluded as an option.
2. **Stagger Morning Chat Shifts:** Introduce a 05:30 or 06:00 IST early-morning sub-pod to clear accumulated overnight chats before the 08:00–10:00 queue peak.
3. **Overnight Handoff from Indore:** Tighten triage protocols between Indore Night shift and morning frontline to prevent chat tickets breaching during shift changeover.
4. **Policy Leakage Elimination:** Institute an automated helpdesk rule blocking simultaneous refunds and replacements for the same order, and audit the 6 identified exception orders.
5. **Illustrative Target Scenario:** Achieving a 15% breach rate scenario would eliminate ~760 breaches, avoiding ~₹266,000 in customer store credits.

---

### 8. Known Limitations & Assumptions
- **Historical P&L Comparison:** Ticket records begin 1 January 2025. Arjun's claim that SLA credit costs tripled since "last summer" (summer 2024) cannot be verified from the ticket dataset alone (*"Available ticket data does not establish the historical P&L comparison"*).
- **Credit Exposure vs Actual Cash P&L:** Breaches generate store credits of ₹350 per Policy §3; avoiding breaches eliminates credit liability, but does not represent direct cash recovery if customer redemption rates vary.

