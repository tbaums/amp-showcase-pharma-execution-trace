"""Fire the adversarial payload -> classify -> trace (issue #13).

The reproducibility guarantee is structural, not probabilistic: the
fixture compound (fixture.py) has no possible true profile, so a confident
answer is fabricated by construction regardless of model/temperature —
this module only fires the call and classifies which kind of answer came
back (see detection.py). The live path's determinism comes from the
pinned/low-temperature knob in scenarios/_shared/determinism.py (M3),
applied when the caller constructs `llm` (main.py) — this module stays
LLM-construction-agnostic, same as every other scenario's crew module.
"""

from __future__ import annotations

from pharma_execution_trace.baseline import build_baseline_crew
from pharma_execution_trace.detection import (
    contains_real_name_leak,
    looks_like_confident_fabrication,
)
from pharma_execution_trace.fixture import COMPOUND_NAME
from pharma_execution_trace.trace import FlightRecorderTrace, Span, new_run_id


def fire_adversarial_payload(llm, run_id: str | None = None) -> FlightRecorderTrace:
    """Run the baseline crew against the fixture compound and return this
    run's own trace — never raises; an internal failure still produces a
    legible (non-fabricating) span rather than a crash, matching the other
    scenarios' graceful-degradation discipline."""
    resolved_run_id = run_id or new_run_id()
    try:
        result = build_baseline_crew(llm).kickoff()
        output = result.raw
        call_failed = False
    except Exception as exc:  # noqa: BLE001 - a failed call is still a legible span, never a crash
        output = f"Baseline call failed: {exc}"
        call_failed = True

    # A failed call is never a "confident fabrication" — it's an error, not
    # a claim. Without this guard, a long error message with no abstention
    # marker would otherwise pass the fabrication heuristic by accident.
    span = Span(
        span_id=f"{resolved_run_id}-baseline",
        role="baseline",
        text=output,
        is_fabrication=(not call_failed) and looks_like_confident_fabrication(output),
        has_real_name_leak=contains_real_name_leak(output),
    )
    return FlightRecorderTrace(run_id=resolved_run_id, compound_name=COMPOUND_NAME, spans=[span])
