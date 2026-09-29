from pathlib import Path
import pytest
import pandas as pd
from vireo.analysis import read_pack, prepare_tickets
from vireo.ai_assistant import (
    get_deterministic_response,
    stream_ai_response,
    answer_general_question,
    is_vireo_query,
    is_mixed_query,
    is_vireo_content,
)

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def tickets_df():
    raw = read_pack(ROOT / "data")
    return prepare_tickets(raw[0], raw[1])


def test_general_question_capital_of_japan(tickets_df):
    """Requirement 1: Normal/general questions must NOT return Vireo SLA analytics."""
    ans = get_deterministic_response("What is the capital of Japan?", tickets_df, tickets_df)
    assert "Tokyo" in ans
    assert "11,200" not in ans
    assert "breach" not in ans.lower()
    assert "Operational Overview" not in ans


def test_general_question_follow_up(tickets_df):
    """Requirement 4: Follow-up question in general context uses previous context."""
    hist = [
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "The capital of Japan is **Tokyo**."},
    ]
    ans = get_deterministic_response("What about France?", tickets_df, tickets_df, history=hist)
    assert "Paris" in ans
    assert "11,200" not in ans


def test_vireo_question_grounding(tickets_df):
    """Requirement 2: Vireo question returns grounded dataset analytics."""
    ans = get_deterministic_response("Explain the Morning shift performance.", tickets_df, tickets_df)
    assert "Morning shift" in ans
    assert "2,018" in ans
    assert "82.7%" in ans
    assert "₹706,300" in ans
    assert is_vireo_content(ans)


def test_vireo_question_follow_up(tickets_df):
    """Requirement 4: Follow-up question resolves Morning shift from context."""
    hist = [
        {"role": "user", "content": "Explain the Morning shift performance."},
        {"role": "assistant", "content": "The Morning shift generates 2,018 breaches..."},
    ]
    ans = get_deterministic_response("How much credit exposure does that represent?", tickets_df, tickets_df, history=hist)
    assert "₹706,300" in ans
    assert "Morning" in ans


def test_mixed_question_separation(tickets_df):
    """Requirement 3: Mixed questions answer both and distinguish general knowledge from Vireo data."""
    q = "What is the capital of Japan and what is Vireo's SLA breach rate?"
    ans = get_deterministic_response(q, tickets_df, tickets_df)
    assert "### General Knowledge" in ans
    assert "Tokyo" in ans
    assert "### Vireo Support Operations" in ans
    assert "21.79%" in ans or "2,440" in ans or "Operational Overview" in ans


def test_greeting_no_vireo_overview(tickets_df):
    """Greetings should receive conversational greetings, not Vireo SLA overview."""
    ans = get_deterministic_response("Good morning!", tickets_df, tickets_df)
    assert "Hello!" in ans
    assert "Operational Overview" not in ans


def test_offline_fallback_does_not_return_vireo_analytics(tickets_df):
    """Requirement 5 & 6: Offline open-ended queries return clear fallback, not Vireo SLA overview."""
    ans = get_deterministic_response("How does quantum superposition work?", tickets_df, tickets_df)
    assert "offline mode" in ans
    assert "OPENAI_API_KEY" in ans or "GEMINI_API_KEY" in ans
    assert "Operational Overview" not in ans
    assert "11,200 audited tickets" not in ans


def test_delete_individual_conversation_active(tmp_path):
    """Deleting currently open conversation removes it, starts new empty chat, and persists."""
    from vireo.ai_assistant import load_conversations, delete_conversation
    
    test_file = tmp_path / "test_conversations.json"
    convs = load_conversations(test_file)
    assert "conv_morning" in convs
    assert "conv_credit" in convs
    
    # Delete active conv_morning
    updated_convs, new_active = delete_conversation(
        convs,
        cid_to_delete="conv_morning",
        active_cid="conv_morning",
        filepath=test_file,
    )
    
    # 1. conv_morning is removed
    assert "conv_morning" not in updated_convs
    # 2. conv_credit remains untouched
    assert "conv_credit" in updated_convs
    # 3. New empty chat started and set active
    assert new_active != "conv_morning"
    assert new_active in updated_convs
    assert updated_convs[new_active]["messages"] == []
    
    # 4. Verified persistence across reload
    reloaded = load_conversations(test_file)
    assert "conv_morning" not in reloaded
    assert "conv_credit" in reloaded
    assert new_active in reloaded


def test_delete_individual_conversation_inactive(tmp_path):
    """Deleting non-active conversation preserves the active chat and removes only targeted conversation."""
    from vireo.ai_assistant import load_conversations, delete_conversation
    
    test_file = tmp_path / "test_conversations.json"
    convs = load_conversations(test_file)
    
    # Delete inactive conv_credit while conv_morning is open
    updated_convs, new_active = delete_conversation(
        convs,
        cid_to_delete="conv_credit",
        active_cid="conv_morning",
        filepath=test_file,
    )
    
    # 1. conv_credit is removed
    assert "conv_credit" not in updated_convs
    # 2. conv_morning remains open
    assert new_active == "conv_morning"
    assert "conv_morning" in updated_convs
    # 3. conv_chat_voice remains untouched
    assert "conv_chat_voice" in updated_convs
    
    # 4. Verified persistence across reload
    reloaded = load_conversations(test_file)
    assert "conv_credit" not in reloaded
    assert "conv_morning" in reloaded

