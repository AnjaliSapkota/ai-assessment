from langgraph.graph import StateGraph, START, END

from workflow.state import AssessmentState

from workflow.nodes import (
    load_normalized_data,
    reconcile_documents,
    generate_report,
)


def build_graph():
    """Build the assessment LangGraph workflow."""

    graph = StateGraph(AssessmentState)

    graph.add_node(
        "load_data",
        load_normalized_data,
    )

    graph.add_node(
        "reconcile",
        reconcile_documents,
    )

    graph.add_node(
        "generate_report",
        generate_report,
    )

    graph.add_edge(
        START,
        "load_data",
    )

    graph.add_edge(
        "load_data",
        "reconcile",
    )

    graph.add_edge(
        "reconcile",
        "generate_report",
    )

    graph.add_edge(
        "generate_report",
        END,
    )

    return graph.compile()