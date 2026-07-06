"""AMP Flow entrypoint (issue #13) — mirrors the proven Autodesk/no-code-trigger
shape (a `Flow` subclass + a no-argument `kickoff()`), fixing the live-deploy
bug where `type="flow"` requires a real Flow, not a bare function (amp-showcase
#29). The `run_id` is read from env (with a synthetic default of a fresh id per
call) so the deployed crew is runnable for a smoke kickoff; AMP's own
kickoff_id can be supplied live via `SMOKE_RUN_ID` to isolate a real run.

The shared determinism knob (formerly scenarios/_shared/determinism.py, M3) is
INLINED here so the deployed artifact is self-contained — the deploy tree is
only this package, and `scenarios/_shared/` is a test-only harness that is NOT
shipped (amp-showcase #30). The shared module still backs the unit tests.
"""

from __future__ import annotations

import os
from typing import Any

from crewai import LLM
from crewai.flow.flow import Flow, start

from pharma_execution_trace.surface import fire_adversarial_payload

DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"

# Pinned/low-temperature config for ~100% reproducible baseline fabrication.
# Inlined from the shared M3 harness so production code ships without a
# repo-relative import (amp-showcase #30); the shared module still backs tests.
DETERMINISTIC_LLM_CONFIG: dict[str, Any] = {
    "temperature": 0.0,
    "seed": 42,
    "top_p": 1.0,
}


def _deterministic_llm_kwargs(**overrides: Any) -> dict[str, Any]:
    return {**DETERMINISTIC_LLM_CONFIG, **overrides}


class FlightRecorderFlow(Flow):
    @start()
    def fire_and_trace(self) -> dict:
        """AMP's entrypoint contract: fire the fixture's adversarial payload
        and return this run's own trace, isolated by `run_id` (defaults to a
        fresh one per call unless the caller supplies AMP's own kickoff_id via
        `SMOKE_RUN_ID`)."""
        run_id = os.environ.get("SMOKE_RUN_ID") or None
        llm = LLM(**_deterministic_llm_kwargs(model=DEFAULT_MODEL))
        trace = fire_adversarial_payload(llm, run_id=run_id)
        span = trace.fabricating_span()
        return {
            "run_id": trace.run_id,
            "compound_name": trace.compound_name,
            "fabricating_span_id": span.span_id if span else None,
            "incident_report": trace.incident_report(),
        }


def kickoff():
    """AMP deployment entrypoint (no args; mirrors Autodesk/no-code-trigger)."""
    return FlightRecorderFlow().kickoff()


if __name__ == "__main__":
    import json

    print(json.dumps(kickoff(), indent=2, default=str))
