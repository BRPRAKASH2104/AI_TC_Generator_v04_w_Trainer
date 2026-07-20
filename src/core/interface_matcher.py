"""Relevance-scoped system-interface selection for prompts.

Attaching the full global interface dictionary to every requirement makes
prompt size scale as requirements x interfaces (review 2026-07-20, archived
finding 8). This module selects only the interfaces a requirement actually
references by signal name, with a bounded fallback so a requirement that names
no signals still receives interface context.

Matching is token-based on signal-like identifiers. A token counts as a signal
only if it contains an underscore or is at least four characters long, so
ordinary short words (e.g. "CAN", "BUS") do not produce false matches. Exact
token matches are supplemented by a high-cutoff fuzzy pass to tolerate minor
typos in automotive signal names.
"""

import re
from difflib import get_close_matches
from typing import Any

# Cap on the number of interfaces attached to any single requirement. Bounds
# the worst case (no matches -> capped fallback) so prompt growth stays linear
# in requirements rather than requirements x interfaces.
MAX_INTERFACES_PER_REQUIREMENT = 40

# Cutoff for the fuzzy signal-name match (0..1); high to avoid false positives.
_FUZZY_CUTOFF = 0.9

# Identifier-like tokens (letters, digits, underscore) of length >= 3.
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")

type Interface = dict[str, Any]
type InterfaceIndex = list[tuple[frozenset[str], Interface]]


def _signal_tokens(text: str) -> set[str]:
    """Extract signal-like tokens from text (upper-cased, filtered)."""
    tokens: set[str] = set()
    for tok in _TOKEN_RE.findall(text.upper()):
        if "_" in tok or len(tok) >= 4:
            tokens.add(tok)
    return tokens


def interface_signals(interface: Interface) -> frozenset[str]:
    """Signal-name tokens that identify an interface (from id, name, text)."""
    signals: set[str] = set()
    for key in ("id", "name", "text"):
        signals |= _signal_tokens(str(interface.get(key, "")))
    return frozenset(signals)


def build_interface_index(interfaces: list[Interface]) -> InterfaceIndex:
    """Pre-compute (signals, interface) pairs once per requirement set."""
    return [(interface_signals(iface), iface) for iface in interfaces]


def select_relevant_interfaces(
    requirement_text: str,
    info_texts: list[str],
    interface_index: InterfaceIndex,
    cap: int = MAX_INTERFACES_PER_REQUIREMENT,
) -> list[Interface]:
    """Return the interfaces relevant to a requirement.

    An interface is relevant when one of its signal tokens appears in the
    requirement text or its nearby information (exact or high-cutoff fuzzy).

    Args:
        requirement_text: The requirement's normalised text.
        info_texts: Normalised text of information artifacts near the requirement.
        interface_index: Output of `build_interface_index` for the global set.
        cap: Maximum interfaces to return.

    Returns:
        Matched interfaces (capped). If nothing matches, the full list capped
        at `cap` (bounded fallback), so interface context is never fully lost.
    """
    req_tokens = _signal_tokens(" ".join([requirement_text, *info_texts]))

    matched: list[Interface] = []
    for signals, iface in interface_index:
        if (
            signals & req_tokens
            or req_tokens
            and any(
                get_close_matches(signal, req_tokens, n=1, cutoff=_FUZZY_CUTOFF)
                for signal in signals
            )
        ):
            matched.append(iface)

    if not matched:
        return [iface for _, iface in interface_index[:cap]]
    return matched[:cap]
