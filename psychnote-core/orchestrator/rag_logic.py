"""
Compatibility shim: re-exports orchestrator_graph elements.
Deprecated: Use orchestrator.orchestrator_graph instead.
"""
from orchestrator.orchestrator_graph import (
    AgentState,
    PsychiatricOrchestrator,
)

__all__ = ["AgentState", "PsychiatricOrchestrator"]