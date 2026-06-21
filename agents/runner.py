from typing import Optional

from .researcher import research_agent
from .writer import writer_agent
from .editor import editor_agent


def run_agents(question: str, context: Optional[str]) -> dict:
    """Orchestrate researcher -> writer -> editor.

    - If `context` is provided, include it with the question for the researcher.
    - If no context, researcher receives only the question.

    Returns a dict with intermediate and final outputs.
    """
    if context:
        researcher_input = f"Context:\n{context}\n\nQuestion:\n{question}"
    else:
        researcher_input = question

    result = {
        "question": question,
        "context_present": bool(context),
        "research": None,
        "written": None,
        "final": None,
    }

    # Research
    research_out = research_agent(researcher_input)
    result["research"] = research_out

    # Write
    written_out = writer_agent(research_out)
    result["written"] = written_out

    # Edit
    edited_out = editor_agent(written_out)
    result["final"] = edited_out

    return result
