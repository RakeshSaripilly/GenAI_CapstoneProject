from typing import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph import END

from agents.researcher import research_agent
from agents.writer import writer_agent
from agents.editor import editor_agent
from evaluation.evaluator import evaluate


class AgentState(TypedDict):

    topic: str
    context: str
    research: str
    article: str
    edited: str
    evaluation: dict


def research_node(state):
    try:
        researcher_input = state["topic"]
        if state.get("context"):
            researcher_input = f"Context:\n{state['context']}\n\nQuestion:\n{state['topic']}"

        research = research_agent(
            researcher_input
        )
        return {"research": research}
    except Exception as e:
        raise Exception(f"Research node failed: {str(e)}")


def writer_node(state):
    try:
        article = writer_agent(
            state["research"]
        )
        return {"article": article}
    except Exception as e:
        raise Exception(f"Writer node failed: {str(e)}")


def editor_node(state):
    try:
        edited = editor_agent(
            state["article"]
        )
        return {"edited": edited}
    except Exception as e:
        raise Exception(f"Editor node failed: {str(e)}")


def evaluation_node(state):

    result = evaluate(
        state["edited"]
    )

    return {"evaluation": result}


builder = StateGraph(
    AgentState
)

builder.add_node(
    "research",
    research_node
)

builder.add_node(
    "writer",
    writer_node
)

builder.add_node(
    "editor",
    editor_node
)

builder.add_node(
    "evaluation",
    evaluation_node
)

builder.set_entry_point(
    "research"
)

builder.add_edge(
    "research",
    "writer"
)

builder.add_edge(
    "writer",
    "editor"
)

builder.add_edge(
    "editor",
    "evaluation"
)

builder.add_edge(
    "evaluation",
    END
)

graph = builder.compile()


def run_graph_flow(question: str, context: str = "") -> dict:
    """Run the compiled graph with an optional retrieved context."""
    initial_state = {
        "topic": question,
        "context": context,
        "research": "",
        "article": "",
        "edited": "",
        "evaluation": {},
    }
    return graph.invoke(initial_state)
