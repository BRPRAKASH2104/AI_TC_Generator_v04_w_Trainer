"""Tests for relevance-scoped interface selection (archived finding 8)."""

from src.core.interface_matcher import (
    build_interface_index,
    interface_signals,
    select_relevant_interfaces,
)


def _index(interfaces):
    return build_interface_index(interfaces)


def test_signals_ignore_short_common_words():
    # "CAN"/"BUS"/"LIN" are short common words and must not become signals.
    assert interface_signals({"id": "IF_1", "name": "CAN Bus"}) == frozenset({"IF_1"})


def test_underscore_and_long_tokens_are_signals():
    sig = interface_signals({"id": "B_VEHICLE_MOVING", "text": "Motion sensor"})
    assert "B_VEHICLE_MOVING" in sig
    assert "MOTION" in sig  # length >= 4
    assert "SENSOR" in sig


def test_exact_match_scopes_to_referenced_interface():
    interfaces = [
        {"id": "B_VEHICLE_MOVING", "text": "Motion"},
        {"id": "B_DOOR_OPEN", "text": "Door position"},
    ]
    result = select_relevant_interfaces(
        "Lock when B_VEHICLE_MOVING is true", [], _index(interfaces)
    )
    assert len(result) == 1
    assert result[0]["id"] == "B_VEHICLE_MOVING"


def test_info_text_contributes_to_matching():
    interfaces = [{"id": "B_DOOR_OPEN", "text": "Door"}, {"id": "B_SPEED", "text": "Speed"}]
    result = select_relevant_interfaces(
        "Generic requirement text",
        ["Depends on B_DOOR_OPEN state"],
        _index(interfaces),
    )
    assert [i["id"] for i in result] == ["B_DOOR_OPEN"]


def test_no_match_falls_back_to_all_capped():
    interfaces = [{"id": "IF_001", "name": "CAN Bus"}, {"id": "IF_002", "name": "LIN Bus"}]
    result = select_relevant_interfaces(
        "Door shall lock when vehicle speed exceeds threshold", [], _index(interfaces)
    )
    # Nothing referenced -> bounded fallback returns the full (small) list.
    assert len(result) == 2


def test_fallback_is_capped():
    interfaces = [{"id": f"SIGNAL_UNREFERENCED_{i}"} for i in range(100)]
    result = select_relevant_interfaces("no signals here", [], _index(interfaces), cap=40)
    assert len(result) == 40


def test_matched_results_are_capped():
    interfaces = [{"id": f"SIG_{i}"} for i in range(60)]
    text = " ".join(f"SIG_{i}" for i in range(60))
    result = select_relevant_interfaces(text, [], _index(interfaces), cap=40)
    assert len(result) == 40


def test_fuzzy_match_tolerates_typo():
    interfaces = [{"id": "B_VEHICLE_MOVING"}]
    # One transposed/dropped char -> close match above the 0.9 cutoff.
    result = select_relevant_interfaces("check B_VEHICLE_MOVNG signal", [], _index(interfaces))
    assert len(result) == 1


def test_short_word_does_not_false_match():
    interfaces = [{"id": "IF_1", "name": "CAN Bus"}]
    # "can" appears as an ordinary word but must not match the CAN interface
    # (it is not a qualifying signal), so this falls back to all (the 1 iface).
    result = select_relevant_interfaces("the door can be locked", [], _index(interfaces))
    # Fallback returns the single interface; assert no *exact* signal match
    # inflated behaviour by checking a two-interface disambiguation instead.
    interfaces2 = [
        {"id": "IF_CAN", "name": "CAN Bus"},
        {"id": "B_DOOR_LOCK", "text": "Lock"},
    ]
    result2 = select_relevant_interfaces(
        "the door can be locked via B_DOOR_LOCK", [], _index(interfaces2)
    )
    assert [i["id"] for i in result2] == ["B_DOOR_LOCK"]
    assert len(result) == 1
