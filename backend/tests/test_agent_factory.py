"""
Tests for Agent Factory & Instance Caching per spec §24 & §25.1
"""

import pytest
from app.application.agent_factory_service import AgentFactoryService


def test_agent_instance_cache():
    factory = AgentFactoryService()
    config_v1 = {
        "id": "agent-123",
        "name": "Test Agent",
        "version": 1,
        "tools": [{"tool_name": "calculator", "enabled": True}],
        "planning_enabled": False,
    }

    # First access builds and caches
    inst1 = factory.get_or_create_agent(config_v1)
    assert inst1["name"] == "Test Agent"

    # Second access returns cached object
    inst2 = factory.get_or_create_agent(config_v1)
    assert inst1 is inst2

    # Updating version invalidates old cache
    config_v2 = dict(config_v1, version=2, name="Test Agent Updated")
    inst3 = factory.get_or_create_agent(config_v2)
    assert inst3["name"] == "Test Agent Updated"
    assert inst3 is not inst1
