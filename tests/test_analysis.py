from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from vireo.analysis import (
    read_pack,
    prepare_tickets,
    audit_pack,
    weekly_report,
    agent_report,
    channel_report,
    shift_report,
    monthly_report,
    SLA_MINUTES,
    SLA_CREDIT_INR,
)

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def loaded_pack():
    raw = read_pack(ROOT / "data")
    prepared = prepare_tickets(raw[0], raw[1])
    audit = audit_pack(*raw, prepared)
    return raw, prepared, audit


def test_migration_deduplication(loaded_pack):
    raw, df, audit = loaded_pack
    raw_tickets = raw[0]
    assert len(raw_tickets) == 11816
    assert df["ticket_id"].nunique() == 11200
    assert audit.duplicate_ids == 616
    assert audit.duplicate_rows == 1232

    # Verify that all 616 duplicated IDs exist in both source systems in the raw data
    dup_ids = raw_tickets.loc[raw_tickets["ticket_id"].duplicated(keep=False), "ticket_id"].unique()
    assert len(dup_ids) == 616
    dup_raw = raw_tickets[raw_tickets["ticket_id"].isin(dup_ids)]
    source_counts = dup_raw.groupby("ticket_id")["source_system"].nunique()
    assert (source_counts == 2).all()

    # Verify that after deduplication, every single duplicated ticket ID kept the helpdesk version
    dedup_dups = df[df["ticket_id"].isin(dup_ids)]
    assert len(dedup_dups) == 616
    assert (dedup_dups["source_system"] == "helpdesk").all()


def test_sla_thresholds():
    assert SLA_MINUTES["chat"] == 15
    assert SLA_MINUTES["voice"] == 120
    assert SLA_MINUTES["social"] == 240
    assert SLA_MINUTES["email"] == 480
    assert SLA_CREDIT_INR == 350


def test_exact_boundary_behavior(loaded_pack):
    _, df, _ = loaded_pack

    # Policy boundary: response_minutes > target is a breach; exactly at target is NOT a breach
    exact_matches = df[df["response_minutes"] == df["sla_target_minutes"]]
    assert len(exact_matches) == 55
    # All tickets exactly on the SLA threshold must be NOT breached
    assert (exact_matches["sla_breach"] == False).all()
    assert (exact_matches["minutes_late"] == 0).all()
    assert (exact_matches["sla_credit_inr"] == 0).all()

    # Synthetic test to verify strict inequality (> vs >=)
    synth = pd.DataFrame({
        "ticket_id": ["T1", "T2", "T3"],
        "channel": ["chat", "chat", "chat"],
        "created_at": ["2026-01-01 10:00:00", "2026-01-01 10:00:00", "2026-01-01 10:00:00"],
        "first_response_at": ["2026-01-01 10:14:59", "2026-01-01 10:15:00", "2026-01-01 10:15:01"],
        "resolved_at": ["2026-01-01 11:00:00", "2026-01-01 11:00:00", "2026-01-01 11:00:00"],
        "source_system": ["helpdesk", "helpdesk", "helpdesk"],
        "customer_id": ["C1", "C2", "C3"],
        "agent_id": ["A1001", "A1001", "A1001"],
        "order_id": [None, None, None],
        "product_sku": ["P1", "P1", "P1"],
        "csat_score": [None, None, None],
        "refund_amount_inr": [None, None, None],
        "replacement_issued": ["N", "N", "N"],
        "customer_message": ["hi", "hi", "hi"],
    })
    agents_df = pd.DataFrame([{
        "agent_id": "A1001", "name": "Agent 1", "site": "Bengaluru",
        "team": "Chat Frontline", "shift": "Morning", "tier": 1,
        "from_date": "2025-01-01", "to_date": None
    }])
    synth_prep = prepare_tickets(synth, agents_df)
    # T1: 14m59s -> no breach
    assert not synth_prep.loc[synth_prep["ticket_id"] == "T1", "sla_breach"].values[0]
    # T2: exactly 15m -> NO breach (strict >)
    assert not synth_prep.loc[synth_prep["ticket_id"] == "T2", "sla_breach"].values[0]
    # T3: 15m01s -> breach
    assert synth_prep.loc[synth_prep["ticket_id"] == "T3", "sla_breach"].values[0]


def test_utc_to_ist_conversion(loaded_pack):
    _, df, _ = loaded_pack
    # All timestamps must be converted to Asia/Kolkata
    assert str(df["created_at_ist"].dt.tz) == "Asia/Kolkata"
    assert str(df["first_response_at_ist"].dt.tz) == "Asia/Kolkata"

    # Invariant: elapsed response duration in minutes must be identical in UTC vs IST
    utc_duration = (df["first_response_at"] - df["created_at"]).dt.total_seconds() / 60
    ist_duration = (df["first_response_at_ist"] - df["created_at_ist"]).dt.total_seconds() / 60
    assert np.allclose(utc_duration, ist_duration)

    # Offset check: IST is UTC + 5h30m
    sample = df.iloc[0]
    offset = (sample["created_at_ist"].to_pydatetime().replace(tzinfo=None)
              - sample["created_at"].to_pydatetime().replace(tzinfo=None)).total_seconds()
    assert offset == 19800  # 5.5 hours * 3600


def test_roster_date_matching_and_june_changes(loaded_pack):
    raw, df, audit = loaded_pack
    assert audit.unmatched_roster == 0
    assert df["shift"].isna().sum() == 0

    # Roster has 46 rows for 44 agents
    agents_raw = raw[1]
    assert len(agents_raw) == 46
    assert agents_raw["agent_id"].nunique() == 44

    # Agents A3002 and A3003 moved from Night to Day on 2025-06-30
    for aid in ["A3002", "A3003"]:
        t_agent = df[df["agent_id"] == aid]
        before = t_agent[t_agent["ticket_date"] <= pd.Timestamp("2025-06-29").date()]
        after = t_agent[t_agent["ticket_date"] >= pd.Timestamp("2025-06-30").date()]
        assert len(before) > 0 and (before["shift"] == "Night").all()
        assert len(after) > 0 and (after["shift"] == "Day").all()


def test_csat_normalization(loaded_pack):
    raw, df, _ = loaded_pack
    raw_tickets = raw[0]
    # In raw: 2,066 tickets have score 0
    assert int((pd.to_numeric(raw_tickets["csat_score"], errors="coerce") == 0).sum()) == 2066
    # In deduplicated: 1,730 tickets have score 0
    assert int((pd.to_numeric(df["csat_score"], errors="coerce") == 0).sum()) == 1730
    # In clean CSAT: 0s converted to NaN, no 0s remain
    assert df["csat_clean"].eq(0).sum() == 0
    assert df["csat_clean"].isna().sum() == 1730 + int(df["csat_score"].isna().sum())
    # Preserves 1..5 values
    valid_scores = df["csat_clean"].dropna()
    assert valid_scores.between(1, 5).all()


def test_weekly_grouping_and_partial_weeks(loaded_pack):
    _, df, _ = loaded_pack
    w = weekly_report(df)
    assert len(w) == 79
    # Required columns present
    for col in ["week_start", "week_end", "tickets", "breaches", "breach_rate", "sla_credit_exposure", "partial_week"]:
        assert col in w.columns

    # Monday start check
    assert all(pd.to_datetime(d).weekday() == 0 for d in w["week_start"])
    # Sunday end check
    assert all(pd.to_datetime(d).weekday() == 6 for d in w["week_end"])

    # Partial weeks identification
    partial_starts = w[w["partial_week"]]["week_start"].tolist()
    assert pd.Timestamp("2024-12-30").date() in partial_starts  # Jan 1-5, 2025 (5 days)
    assert pd.Timestamp("2026-06-29").date() in partial_starts  # Jun 29-30, 2026 (2 days)


def test_credit_calculation_and_baseline(loaded_pack):
    _, df, _ = loaded_pack
    assert len(df) == 11200
    assert int(df["sla_breach"].sum()) == 2440
    assert round(float(df["sla_breach"].mean()) * 100, 2) == 21.79
    assert int(df["sla_credit_inr"].sum()) == 854000
    assert (df.loc[df["sla_breach"], "sla_credit_inr"] == 350).all()
    assert (df.loc[~df["sla_breach"], "sla_credit_inr"] == 0).all()
    assert (df.loc[df["sla_breach"], "minutes_late"] > 0).all()
    assert (df.loc[~df["sla_breach"], "minutes_late"] == 0).all()


def test_channel_baseline(loaded_pack):
    _, df, _ = loaded_pack
    cr = channel_report(df).set_index("channel")
    assert cr.loc["chat", "tickets"] == 4959 and cr.loc["chat", "breaches"] == 1368
    assert cr.loc["email", "tickets"] == 3647 and cr.loc["email", "breaches"] == 745
    assert cr.loc["social", "tickets"] == 1106 and cr.loc["social", "breaches"] == 243
    assert cr.loc["voice", "tickets"] == 1488 and cr.loc["voice", "breaches"] == 84


def test_shift_baseline(loaded_pack):
    _, df, _ = loaded_pack
    sr = shift_report(df).set_index("shift")
    assert sr.loc["Morning", "tickets"] == 6264 and sr.loc["Morning", "breaches"] == 2018
    assert sr.loc["Day", "tickets"] == 4668 and sr.loc["Day", "breaches"] == 393
    assert sr.loc["Night", "tickets"] == 268 and sr.loc["Night", "breaches"] == 29


def test_agent_report_structure(loaded_pack):
    _, df, _ = loaded_pack
    ar = agent_report(df)
    # Roster has 44 agents; 2 agents changed shifts, resulting in 46 agent-shift combinations
    assert len(ar) == 46
    for col in ["agent_id", "agent_name", "site", "team", "shift", "tier", "ticket_volume", "breach_count", "breach_rate", "sla_credit_exposure"]:
        assert col in ar.columns
    # Check Tier 2 separation: Tier 2 agents must be present with tier == 2
    assert (ar["tier"] == 2).sum() > 0


def test_refund_replacement_policy_exception(loaded_pack):
    _, _, audit = loaded_pack
    assert audit.refund_replacement_exceptions == 6


def test_ivr_investigation_metrics(loaded_pack):
    _, _, audit = loaded_pack
    ivr = audit.ivr_investigation
    assert ivr["total_voice_tickets"] == 1488
    assert ivr["ivr_transcript_tickets_voice"] == 902
    assert ivr["ivr_transcript_tickets_all"] == 916
    assert ivr["audio_artifact_tags"] == 14
    # Matches Sameer's email claim: "About forty messages are failed IVR transcripts"
    assert ivr["failure_wording_in_ivr"] == 44


def test_monthly_report_finance(loaded_pack):
    _, df, _ = loaded_pack
    m = monthly_report(df)
    assert len(m) == 18
    # Early 2025 (Jan-Jun) credits were ~₹7,350 to ₹14,350
    assert m[m["month"] < "2025-07"]["sla_credit_exposure"].max() <= 15000
    # From Aug 2025 onwards, credits were ~₹54,950 to ₹74,550
    assert m[m["month"] >= "2025-08"]["sla_credit_exposure"].min() >= 50000

