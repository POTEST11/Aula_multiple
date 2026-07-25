"""Activity generation graph built with LangGraph.

Defines the sequential 4-node pipeline for generating multi-grade
educational activities.
"""

from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    activity_design,
    curriculum_analysis,
    output_formatting,
    resource_adaptation,
)
from app.agent.state import AgentState


def build_activity_graph() -> StateGraph:
    """Build the sequential 4-node graph for activity generation.

    The pipeline executes:
      1. curriculum_analysis - Retrieves relevant curriculum standards via RAG
      2. activity_design - Generates anchor activity and variant drafts
      3. resource_adaptation - Adapts drafts to available resources
      4. output_formatting - Produces final structured ActivityOutput

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(AgentState)

    graph.add_node("curriculum_analysis", curriculum_analysis.run)
    graph.add_node("activity_design", activity_design.run)
    graph.add_node("resource_adaptation", resource_adaptation.run)
    graph.add_node("output_formatting", output_formatting.run)

    graph.set_entry_point("curriculum_analysis")
    graph.add_edge("curriculum_analysis", "activity_design")
    graph.add_edge("activity_design", "resource_adaptation")
    graph.add_edge("resource_adaptation", "output_formatting")
    graph.add_edge("output_formatting", END)

    return graph.compile()
