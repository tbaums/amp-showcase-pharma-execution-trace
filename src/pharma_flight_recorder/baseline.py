"""The baseline crew (issue #13).

Deliberately has NO instruction to hedge or abstain — unlike #11's
enrichment crew, which explicitly tells the agent to say "nothing
meaningful is known" for an unfamiliar name. Here the point is the
opposite: this is the crew an attendee would write without knowing better,
run once locally (OSS, no trace) and once against the managed endpoint
(trace visible) with the IDENTICAL payload — same code, same fixture, two
environments. `llm` is injected by the caller so this module never
hard-codes a provider.
"""

from __future__ import annotations

from crewai import Agent, Crew, Task

from pharma_flight_recorder.fixture import BASELINE_PROMPT


def build_baseline_crew(llm) -> Crew:
    """A fresh crew per run — never shared/mutated — so each attendee's own
    run_id genuinely corresponds to their own, isolated execution."""
    analyst = Agent(
        role="Pharma Research Analyst",
        goal="Answer questions about a compound's efficacy and safety profile precisely.",
        backstory=(
            "An analyst who answers questions about compounds directly, with specific figures "
            "where possible."
        ),
        llm=llm,
    )
    task = Task(
        description=BASELINE_PROMPT,
        expected_output="A specific efficacy and safety profile, with figures.",
        agent=analyst,
    )
    return Crew(agents=[analyst], tasks=[task])
