from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import numpy as np

SLA_MINUTES = {"chat": 15, "voice": 120, "social": 240, "email": 480}
SLA_CREDIT_INR = 350
SHIFT_ORDER = ["Morning", "Day", "Night"]
CHANNEL_ORDER = ["chat", "email", "social", "voice"]

@dataclass
class Audit:
    raw_rows: int
    unique_ticket_ids: int
    duplicate_ids: int
    duplicate_rows: int
    unmatched_roster: int
    invalid_refs: dict
    missing: dict
    ivr_rows: int
    refund_replacement_exceptions: int
    legacy_csat_zeros_raw: int = 0
    legacy_csat_zeros_dedup: int = 0
    transfers_summary: dict = field(default_factory=dict)
    ivr_investigation: dict = field(default_factory=dict)


def read_pack(data_dir: str | Path):
    p = Path(data_dir)
    tickets = pd.read_csv(p / "tickets.csv")
    agents = pd.read_csv(p / "agents.csv")
    customers = pd.read_csv(p / "customers.csv")
    orders = pd.read_csv(p / "orders.csv")
    products = pd.read_csv(p / "products.csv")
    return tickets, agents, customers, orders, products


def prepare_tickets(tickets: pd.DataFrame, agents: pd.DataFrame) -> pd.DataFrame:
    t = tickets.copy()
    for c in ["created_at", "first_response_at", "resolved_at"]:
        t[c] = pd.to_datetime(t[c], errors="coerce", utc=True)
    a = agents.copy()
    a["from_date"] = pd.to_datetime(a["from_date"], errors="coerce").dt.date
    a["to_date"] = pd.to_datetime(a["to_date"], errors="coerce").dt.date

    # Migration duplicates: prioritize helpdesk over legacy_fd where the same ticket exists in both systems.
    t["_source_rank"] = t["source_system"].map({"helpdesk": 0, "legacy_fd": 1}).fillna(9)
    t = t.sort_values(["ticket_id", "_source_rank"]).drop_duplicates("ticket_id", keep="first").copy()
    t.drop(columns=["_source_rank"], inplace=True)

    # Timezone conversion: API timestamps are UTC, convert to IST (Asia/Kolkata)
    t["created_at_ist"] = t["created_at"].dt.tz_convert("Asia/Kolkata")
    t["first_response_at_ist"] = t["first_response_at"].dt.tz_convert("Asia/Kolkata")
    t["resolved_at_ist"] = t["resolved_at"].dt.tz_convert("Asia/Kolkata")
    t["created_ist"] = t["created_at_ist"]  # backward compatibility alias

    # SLA deterministic engine
    t["response_minutes"] = (t["first_response_at"] - t["created_at"]).dt.total_seconds() / 60
    t["sla_target_minutes"] = t["channel"].map(SLA_MINUTES)
    # Exact boundary: response_minutes > target is a breach; exactly at target is NOT a breach
    t["sla_breach"] = t["response_minutes"] > t["sla_target_minutes"]
    t["minutes_late"] = (t["response_minutes"] - t["sla_target_minutes"]).clip(lower=0)
    t["sla_credit_inr"] = t["sla_breach"].astype(int) * SLA_CREDIT_INR

    # Weekly reporting: Monday-Sunday weeks in IST
    t["week_start_ist"] = (
        t["created_at_ist"].dt.normalize()
        - pd.to_timedelta(t["created_at_ist"].dt.weekday, unit="D")
    ).dt.date

    # Historical roster matching uses the calendar date in IST; to_date is inclusive for the full day.
    t["ticket_date"] = t["created_at_ist"].dt.date
    roster_cols = ["agent_id", "name", "site", "team", "shift", "tier", "from_date", "to_date"]
    candidates = t[["agent_id", "ticket_date"]].reset_index().merge(a[roster_cols], on="agent_id", how="left")
    valid = candidates[
        (candidates["from_date"] <= candidates["ticket_date"])
        & (candidates["to_date"].isna() | (candidates["to_date"] >= candidates["ticket_date"]))
    ].drop_duplicates("index", keep="first")
    roster_map = valid.set_index("index")[["name", "site", "team", "shift", "tier"]]
    for src, dst in [("name", "agent_name"), ("site", "site"), ("team", "roster_team"), ("shift", "shift"), ("tier", "tier")]:
        t[dst] = roster_map[src].reindex(t.index).values

    # Legacy 0 means no response per policy; convert to NaN
    t["csat_clean"] = pd.to_numeric(t["csat_score"], errors="coerce").replace(0, np.nan)
    t["refund_clean"] = pd.to_numeric(t["refund_amount_inr"], errors="coerce").fillna(0)
    # Policy exception: customer should never receive both refund and replacement
    t["refund_replacement_exception"] = (t["refund_clean"] > 0) & (t["replacement_issued"].astype(str).str.upper() == "Y")
    t["ivr_transcript"] = t["customer_message"].fillna("").astype(str).str.contains(r"\[IVR transcript\]", regex=True)
    # Dataset spans 2025-01-01 (Wed) to 2026-06-30 (Tue), so first and last weeks are partial weeks
    t["partial_week"] = t["week_start_ist"].isin([pd.Timestamp("2024-12-30").date(), pd.Timestamp("2026-06-29").date()])
    return t


def audit_pack(tickets, agents, customers, orders, products, prepared) -> Audit:
    raw_rows = len(tickets)
    unique = tickets["ticket_id"].nunique()
    duplicate_ids = tickets.loc[tickets["ticket_id"].duplicated(keep=False), "ticket_id"].nunique()
    duplicate_rows = int(tickets["ticket_id"].duplicated(keep=False).sum())
    invalid_refs = {
        "customer_id": int((~prepared["customer_id"].isin(customers["customer_id"])).sum()),
        "agent_id": int((~prepared["agent_id"].isin(agents["agent_id"])).sum()),
        "product_sku": int((~prepared["product_sku"].isin(products["sku"])).sum()),
        "order_id_nonblank": int((prepared["order_id"].notna() & ~prepared["order_id"].isin(orders["order_id"])).sum()),
    }
    missing = {
        c: int(tickets[c].isna().sum())
        for c in ["created_at", "first_response_at", "resolved_at", "agent_id", "product_sku"]
    }
    legacy_csat_raw = int((pd.to_numeric(tickets["csat_score"], errors="coerce") == 0).sum())
    legacy_csat_dedup = int((pd.to_numeric(prepared["csat_score"], errors="coerce") == 0).sum())
    transfers_dist = prepared["transfers"].value_counts().to_dict()

    # Detailed IVR analysis
    voice_tickets = int((prepared["channel"] == "voice").sum())
    ivr_total = int(prepared["ivr_transcript"].sum())
    ivr_voice = int((prepared["ivr_transcript"] & (prepared["channel"] == "voice")).sum())
    artifact_pattern = r"\[(?:inaudible|line dropped|crosstalk)\]"
    audio_artifacts = int(prepared["customer_message"].fillna("").str.contains(artifact_pattern, case=False, regex=True).sum())
    fail_wording_ivr = int((
        prepared["ivr_transcript"]
        & prepared["customer_message"].fillna("").str.contains(r"\b(?:fail|failed|failure|dropped|inaudible|disconnect)\b", case=False, regex=True)
    ).sum())

    ivr_investigation = {
        "total_voice_tickets": voice_tickets,
        "ivr_transcript_tickets_all": ivr_total,
        "ivr_transcript_tickets_voice": ivr_voice,
        "audio_artifact_tags": audio_artifacts,
        "failure_wording_in_ivr": fail_wording_ivr,
    }

    return Audit(
        raw_rows, unique, duplicate_ids, duplicate_rows,
        int(prepared["shift"].isna().sum()), invalid_refs, missing,
        ivr_total, int(prepared["refund_replacement_exception"].sum()),
        legacy_csat_zeros_raw=legacy_csat_raw,
        legacy_csat_zeros_dedup=legacy_csat_dedup,
        transfers_summary=transfers_dist,
        ivr_investigation=ivr_investigation,
    )


def summary(df):
    if df.empty:
        return {"tickets": 0, "breaches": 0, "breach_rate": 0.0, "credits": 0}
    return {
        "tickets": len(df),
        "breaches": int(df["sla_breach"].sum()),
        "breach_rate": float(df["sla_breach"].mean()),
        "credits": int(df["sla_credit_inr"].sum()),
    }


def group_report(df, by):
    if df.empty:
        cols = by if isinstance(by, list) else [by]
        return pd.DataFrame(columns=cols + ["tickets", "breaches", "credits", "avg_response_minutes", "breach_rate"])
    g = df.groupby(by, dropna=False).agg(
        tickets=("ticket_id", "size"),
        breaches=("sla_breach", "sum"),
        credits=("sla_credit_inr", "sum"),
        avg_response_minutes=("response_minutes", "mean"),
    ).reset_index()
    g["breach_rate"] = g["breaches"] / g["tickets"]
    return g


def weekly_report(df):
    if df.empty:
        return pd.DataFrame(columns=["week_start", "week_end", "tickets", "breaches", "breach_rate", "sla_credit_exposure", "partial_week"])
    g = group_report(df, "week_start_ist")
    g["week_start"] = pd.to_datetime(g["week_start_ist"]).dt.date
    g["week_end"] = (pd.to_datetime(g["week_start_ist"]) + pd.Timedelta(days=6)).dt.date
    g["sla_credit_exposure"] = g["credits"]
    g["SLA_credit_exposure"] = g["credits"]
    g["week_start_ist"] = pd.to_datetime(g["week_start_ist"])
    g["partial_week"] = g["week_start"].isin([pd.Timestamp("2024-12-30").date(), pd.Timestamp("2026-06-29").date()])
    return g.sort_values("week_start").reset_index(drop=True)


def agent_report(df):
    if df.empty:
        return pd.DataFrame(columns=["agent_id", "agent_name", "site", "team", "shift", "tier", "ticket_volume", "breach_count", "breach_rate", "sla_credit_exposure"])
    g = df.groupby(["agent_id", "agent_name", "site", "roster_team", "shift", "tier"], dropna=False).agg(
        tickets=("ticket_id", "size"),
        breaches=("sla_breach", "sum"),
        credits=("sla_credit_inr", "sum"),
        avg_response_minutes=("response_minutes", "mean"),
    ).reset_index()
    g["breach_rate"] = g["breaches"] / g["tickets"]
    g.rename(columns={
        "roster_team": "team",
        "tickets": "ticket_volume",
        "breaches": "breach_count",
        "credits": "sla_credit_exposure",
    }, inplace=True)
    g["tickets"] = g["ticket_volume"]
    g["breaches"] = g["breach_count"]
    g["credits"] = g["sla_credit_exposure"]
    # Sort neutrally by team and agent name (no punitive ranking)
    return g.sort_values(["tier", "team", "agent_name"]).reset_index(drop=True)


def channel_report(df):
    if df.empty:
        return pd.DataFrame(columns=["channel", "tickets", "breaches", "credits", "avg_response_minutes", "breach_rate", "sla_credit_exposure"])
    g = group_report(df, "channel")
    g["sla_credit_exposure"] = g["credits"]
    # Reindex to standard channel order if present
    order_dict = {c: i for i, c in enumerate(CHANNEL_ORDER)}
    g["_order"] = g["channel"].map(order_dict).fillna(99)
    g = g.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)
    return g


def shift_report(df):
    if df.empty:
        return pd.DataFrame(columns=["shift", "tickets", "breaches", "credits", "avg_response_minutes", "breach_rate", "sla_credit_exposure"])
    g = group_report(df, "shift")
    res = g.set_index("shift").reindex(SHIFT_ORDER).reset_index()
    res["tickets"] = res["tickets"].fillna(0).astype(int)
    res["breaches"] = res["breaches"].fillna(0).astype(int)
    res["credits"] = res["credits"].fillna(0).astype(int)
    res["breach_rate"] = np.where(res["tickets"] > 0, res["breaches"] / res["tickets"], 0.0)
    res["sla_credit_exposure"] = res["credits"]
    return res


def monthly_report(df):
    if df.empty:
        return pd.DataFrame(columns=["month", "tickets", "breaches", "breach_rate", "sla_credit_exposure", "mean_csat", "csat_responses"])
    temp = df.copy()
    temp["month"] = temp["created_at_ist"].dt.strftime("%Y-%m")
    m = temp.groupby("month").agg(
        tickets=("ticket_id", "size"),
        breaches=("sla_breach", "sum"),
        sla_credit_exposure=("sla_credit_inr", "sum"),
        csat_responses=("csat_clean", "count"),
        mean_csat=("csat_clean", "mean"),
    ).reset_index()
    m["breach_rate"] = m["breaches"] / m["tickets"]
    m["credits"] = m["sla_credit_exposure"]
    return m.sort_values("month").reset_index(drop=True)


def target_impact(df, target_rate: float):
    current_breaches = int(df["sla_breach"].sum())
    target_breaches = int(round(len(df) * target_rate))
    avoided = max(0, current_breaches - target_breaches)
    return {
        "current_breaches": current_breaches,
        "target_breaches": target_breaches,
        "avoided_breaches": avoided,
        "credit_saving_inr": avoided * SLA_CREDIT_INR,
    }

