"""AI orchestration layer: LangGraph agents/graph, the confidence + classification models,
and the embeddings wrapper. Packaged as a path dependency of backend/, sharing its virtual
environment rather than getting its own — see docs/architecture.md's "Resolved decisions"
for why.
"""
