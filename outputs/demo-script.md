# Vireo Audio Support SLA Control Room — 3-Minute Demonstration Script

**Format:** Walkthrough presentation with live screen recording  
**Target Duration:** ~3 minutes (180 seconds)  
**Presenter:** Operations Analytics Lead  

---

### [0:00 – 0:25] 1. The Problem
*(Visual: Open dashboard showing top KPI cards)*
> "Welcome. Vireo Audio leadership needed a reliable, weekly first-response SLA breach report by agent and shift to resolve conflicting claims across departments. Neha observed that the morning team drives most breaches; Priya noted the morning chat team feels demoralized opening to a 'wall of red'; and Arjun in Finance noted SLA credit costs tripled since last summer while headcount is frozen through Q4. Our objective was to audit the raw data, reconcile policy rules, and provide an auditable operational control room."

---

### [0:25 – 0:50] 2. The Prompt & AI-Assisted Development
*(Visual: Show repository structure and test suite in terminal)*
> "We used an AI-assisted development workflow to translate Vireo's Support Operating Policy v3.2 and raw exports into clean, deterministic Python modules. Rather than asking an LLM to perform calculations or building an over-engineered stack, we guided the AI assistant to implement deterministic business logic in Pandas and Streamlit, with pytest enforcing policy rules and regression baselines."

---

### [0:50 – 1:25] 3. The Working Tool & 4. Key Findings
*(Visual: Scroll smoothly through Executive Summary, Weekly Trend, Shift View, and Channel Breakdown)*
> "Here is the working application. On load, the executive cards show the verified baseline: **11,200 unique tickets, 2,440 first-response breaches (a 21.79% breach rate), and ₹854,000 in SLA-credit exposure** at ₹350 per breach.
>
> In the **Weekly Trend**, Monday-to-Sunday weeks are evaluated in IST, with partial weeks at dataset boundaries clearly flagged.
>
> In the **Shift View**, the data validates Neha's observation: **Morning shift accounts for 2,018 of the 2,440 breaches (82.7%)**, with a 32.22% breach rate, compared to 8.42% for Day and 10.82% for Night. However, our shift drill-down shows Morning also handles 56% of total ticket volume. 
>
> In the **Channel View**, Chat has a 27.59% breach rate driven by its strict 15-minute target, generating ₹478,800 in credit exposure."

---

### [1:25 – 1:55] 5. Changes Made & Agent Separation
*(Visual: Switch between Tier 1 and Tier 2 tabs in Agent Report, then open Finance Monthly Check)*
> "In the **Agent Report**, we deliberately avoided a punitive 'worst agent' leaderboard. Denominators are displayed alongside breach rates, and Tier 2 Escalations & Warranty agents are strictly separated into their own view, honoring Policy §6 which states multi-touch warranty cases must not be compared to Tier 1 on volume.
>
> Under the **Finance Monthly Check**, we resolved leadership claims: monthly SLA credits rose from ~₹12k in early 2025 to ~₹70k from August 2025 onwards—supporting Arjun's observation of credit growth—while remaining flat month-on-month between October 2025 and June 2026, confirming Priya's observation. We explicitly note that ticket data begins in 2025, so historical summer 2024 P&L comparisons cannot be established from this dataset."

---

### [1:55 – 2:25] 6. Discarded Approaches
*(Visual: Scroll to Data Quality section and AI Briefing section)*
> "Several architectural decisions were deliberately made:
> - **We discarded React, Next.js, and external databases** in favor of a self-contained, auditable Streamlit architecture with zero infrastructure overhead.
> - **We discarded LLM-based arithmetic, RAG, and LangChain.** Business logic is 100% deterministic; the optional AI briefing receives only verified aggregate metrics and strictly prohibits recommending hiring.
> - **We discarded naive string timestamp offsets** in favor of timezone-aware UTC-to-IST conversion.
> - **We discarded simple pandas deduplication**, building system-aware logic that explicitly prioritizes current Helpdesk records over legacy Freshdesk re-imports."

---

### [2:25 – 3:00] 7. Validation & Wrap-Up
*(Visual: Run pytest in terminal showing 14 passed tests, then click CSV download button)*
> "Finally, the entire pipeline is verified by automated tests:
> - 14 automated pytest cases validate the 616 migration duplicates, exact SLA boundary behavior—where 55 tickets sitting exactly on the SLA threshold are verified non-breaches—roster matching including the June Indore shift changes, CSAT zero-normalization, and the detection of 6 orders violating Policy §5 with simultaneous refunds and replacements.
> - The app provides full CSV downloads for weekly, shift, agent, channel, and data quality reports.
>
> Thank you."

