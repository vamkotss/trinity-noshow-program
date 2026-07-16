"""Tests for the process maps.

WHY TEST A DOCUMENT OF DIAGRAMS
-------------------------------
The process map makes a claim that is easy to state and easy to let rot: every
new step in the redesigned flow traces to a real requirement and a real
stakeholder need. IDs get renamed, requirements get merged, and six months later
the map cites FR-11 that no longer exists - a broken promise nobody noticed.

These tests keep the map honest against the traceability module, and check that
the Mermaid diagrams are at least structurally valid so they will actually render
on GitHub rather than showing a broken-diagram box.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from trinity.traceability import NEEDS, REQUIREMENTS

MAP_PATH = Path("docs/process/PROCESS_MAPS.md")


@pytest.fixture(scope="module")
def text():
    if not MAP_PATH.exists():
        pytest.skip("process map not present in this checkout")
    return MAP_PATH.read_text(encoding="utf-8")


def test_every_requirement_cited_in_the_map_exists(text):
    """The process map does not cite a requirement that has been removed or renamed.

    A dangling FR reference means the redesign points at a requirement that no
    longer exists - the map and the BRD have drifted apart, and the traceability
    the whole project rests on is quietly broken.
    """
    cited = set(re.findall(r"FR-\d+", text))
    dangling = cited - set(REQUIREMENTS)

    assert not dangling, f"process map cites non-existent requirements: {sorted(dangling)}"


def test_every_need_cited_in_the_map_exists(text):
    """Same, for stakeholder needs."""
    cited = set(re.findall(r"N-\d+", text))
    dangling = cited - set(NEEDS)

    assert not dangling, f"process map cites non-existent needs: {sorted(dangling)}"


def test_the_map_has_both_an_as_is_and_a_to_be(text):
    """A redesign needs a before and an after. One without the other is not a redesign.

    The value of a process map is the DELTA between current and proposed. A to-be
    with no as-is is a wish list; an as-is with no to-be is a complaint.
    """
    assert "As-is" in text or "as-is" in text
    assert "To-be" in text or "to-be" in text


def test_both_diagrams_are_present_and_balanced(text):
    """Two Mermaid flowcharts, each opened and closed.

    An unclosed code fence renders as a wall of raw text on GitHub. Cheap to
    check, embarrassing to miss.
    """
    fences = text.count("```mermaid")
    closes = text.count("```")

    assert fences == 2, f"expected 2 mermaid diagrams, found {fences}"
    # Each ```mermaid has a matching closing ```, so total ``` is even.
    assert closes % 2 == 0, "a code fence is unclosed - the diagram will not render"


def test_the_overbooking_downside_is_acknowledged(text):
    """The map must show the overbooking failure case, not just the happy path.

    Dr. Raghavan's objection is that overbooking makes patients wait. If the map
    only showed overbooking working, it would be exactly the naive artefact she
    would tear apart. The 'both patients arrive' branch is what makes the map
    honest - and this test guards it.
    """
    lowered = text.lower()

    assert "collision" in lowered, "the map does not track overbook collisions"
    assert "high-risk" in lowered or "high risk" in lowered, (
        "the map does not restrict overbooking to high-risk slots"
    )


def test_the_to_be_steps_trace_to_requirements(text):
    """The redesign's mapping table links new steps to requirements.

    This is the sentence that separates a process redesign from a brainstorm:
    every new box closes a documented failure and satisfies a documented
    requirement.
    """
    # The to-be section must contain a table mapping steps to FR and N ids.
    assert "Requirement" in text and "Need" in text
    # At least four requirements are referenced (the four interventions).
    cited_frs = set(re.findall(r"FR-\d+", text))
    assert len(cited_frs) >= 4, f"only {len(cited_frs)} requirements traced in the map"
