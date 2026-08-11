"""LangGraph pipeline: classify -> retrieve -> draft -> score.

classify and retrieve are real (ai/models/ classifier, ai/embeddings/ + pgvector).
draft and score are explicit NotImplementedError stubs — the graph shape is final so
wiring in the LLM provider and confidence model later doesn't require restructuring
this graph, but nothing here fakes those two stages.
"""

from langgraph.graph import END, START, StateGraph

from .nodes import classify_node, draft_node, retrieve_node, score_node
from .state import TicketState

_builder = StateGraph(TicketState)
_builder.add_node("classify", classify_node)
_builder.add_node("retrieve", retrieve_node)
_builder.add_node("draft", draft_node)
_builder.add_node("score", score_node)

_builder.add_edge(START, "classify")
_builder.add_edge("classify", "retrieve")
_builder.add_edge("retrieve", "draft")
_builder.add_edge("draft", "score")
_builder.add_edge("score", END)

graph = _builder.compile()
