"""
Tests for Agent Factory & Instance Caching with CompiledStateGraph per spec §24 & §25.1
"""

import pytest
from app.application.agent_factory_service import AgentFactoryService
from langgraph.graph.state import CompiledStateGraph


def test_agent_instance_cache():
    factory = AgentFactoryService()
    config_v1 = {
        "id": "agent-123",
        "name": "Test Agent",
        "version": 1,
        "tools": [{"tool_name": "calculator", "enabled": True}],
        "planning_enabled": False,
    }

    # First access builds CompiledStateGraph via create_deep_agent
    inst1 = factory.get_or_create_agent(config_v1)
    assert inst1 is not None
    assert isinstance(inst1, CompiledStateGraph)

    # Second access returns cached object
    inst2 = factory.get_or_create_agent(config_v1)
    assert inst1 is inst2

    # Updating version invalidates old cache and creates a new compiled graph
    config_v2 = dict(config_v1, version=2, name="Test Agent Updated")
    inst3 = factory.get_or_create_agent(config_v2)
    assert isinstance(inst3, CompiledStateGraph)
    assert inst3 is not inst1
