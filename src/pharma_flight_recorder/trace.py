"""Per-run trace/span model + incident report (issue #13).

Models what the managed trace shows for one run: the specific span where
the baseline fabricated its claim, identifiable by run_id — never a bare
pass/fail, since "open the trace and find the span" is the whole hands-on
act this scenario is built around.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    span_id: str
    role: str
    text: str
    is_fabrication: bool
    has_real_name_leak: bool = False


@dataclass(frozen=True)
class FlightRecorderTrace:
    run_id: str
    compound_name: str
    spans: list[Span] = field(default_factory=list)

    def fabricating_span(self) -> Span | None:
        """The specific span where the baseline fabricated its claim, or
        None if this run didn't fabricate — issue #13 acceptance: RED if
        the span isn't identifiable when a fabrication occurred."""
        for span in self.spans:
            if span.is_fabrication:
                return span
        return None

    def incident_report(self) -> str:
        """The one-line incident report the attendee writes after finding
        the fabricating span."""
        span = self.fabricating_span()
        if span is None:
            return f"Run {self.run_id}: no fabrication detected for {self.compound_name}."
        preview = span.text.strip().replace("\n", " ")[:120]
        return (
            f"Run {self.run_id}: baseline fabricated a confident but false claim about "
            f"{self.compound_name} (no true profile exists) in span {span.span_id!r}: "
            f"{preview!r}"
        )


def new_run_id() -> str:
    return str(uuid.uuid4())
