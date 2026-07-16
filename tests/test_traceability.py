"""Tests for the traceability matrix.

WHAT THESE ENFORCE
------------------
The matrix makes a promise: every stakeholder need is addressed, and every
requirement is justified. These tests make that promise true rather than
decorative.

The failure they exist to catch is the quiet one - a requirement gets deleted, a
need gets added in a later interview, and the matrix silently no longer covers
what it claims to. A generated-and-tested matrix cannot drift that way.
"""

from __future__ import annotations

import pytest

from trinity.traceability import NEEDS, REQUIREMENTS, build, render, verify


def test_the_matrix_verifies_clean():
    """No dangling links, no orphans, no dropped needs."""
    problems = verify()

    assert problems == [], "traceability problems:\n  " + "\n  ".join(problems)


def test_every_requirement_traces_to_a_real_need():
    """No requirement cites a need that does not exist, and none has zero needs.

    A requirement with no need behind it is scope creep wearing an ID.
    """
    for req_id, req in REQUIREMENTS.items():
        assert req["needs"], f"{req_id} has no need behind it"
        for need_id in req["needs"]:
            assert need_id in NEEDS, f"{req_id} cites non-existent need {need_id}"


def test_every_need_is_addressed():
    """No stakeholder need is left without a requirement.

    A need raised in discovery and then not addressed is a promise quietly
    broken - the exact thing that makes a sponsor stop trusting an analyst.
    """
    addressed = {n for req in REQUIREMENTS.values() for n in req["needs"]}

    for need_id, (who, what) in NEEDS.items():
        assert need_id in addressed, f"{need_id} ({who}: {what}) is not addressed"


def test_the_adversarys_concern_is_addressed():
    """Dr. Raghavan's patient-safety concern must map to a requirement.

    This is the concern most likely to sink the business case in the board room.
    If it were not traceable to a requirement, the case would walk into that room
    unprepared for its hardest question.
    """
    # N-06 is the safety concern; N-10 is the hostile-review concern.
    for need_id in ["N-06", "N-10"]:
        addressing = [r for r, req in REQUIREMENTS.items() if need_id in req["needs"]]
        assert addressing, f"{need_id} (Raghavan) is not addressed by any requirement"


def test_the_sponsors_core_need_is_addressed():
    """The COO's need for a defensible cost number (N-01) maps to a requirement."""
    addressing = [r for r, req in REQUIREMENTS.items() if "N-01" in req["needs"]]

    assert addressing, "the sponsor's central need is not addressed"


def test_the_matrix_renders_both_directions():
    """The rendered document contains a forward and a backward trace."""
    text = render()

    assert "Forward trace" in text
    assert "Backward trace" in text

    # Every requirement and need ID appears in the rendered matrix.
    for req_id in REQUIREMENTS:
        assert req_id in text
    for need_id in NEEDS:
        assert need_id in text


def test_build_refuses_to_write_a_broken_matrix(tmp_path, monkeypatch):
    """If a link breaks, generation FAILS rather than writing a false matrix.

    A matrix that claims full coverage while missing a need is worse than none -
    it is a false assurance. Generation must refuse.
    """
    # Break the links: add a need nothing addresses.
    monkeypatch.setitem(NEEDS, "N-99", ("Ghost", "a need nobody addresses"))

    with pytest.raises(ValueError, match="verification failed"):
        build(tmp_path / "TRACEABILITY.md")
