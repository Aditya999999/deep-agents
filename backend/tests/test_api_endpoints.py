"""
Integration tests for FastAPI REST and Streaming endpoints per spec §25.2 & §25.3
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.db.sqlite import init_db, async_session_factory
from app.application.tool_service import ToolService


@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_agent_config_and_tools_flow():
    await init_db()
    # Seed built-in tools
    async with async_session_factory() as session:
        tool_service = ToolService(session)
        await tool_service.ensure_builtin_tools()
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Check tools are seeded
        tools_resp = await client.get("/api/tools")
        assert tools_resp.status_code == 200
        tool_names = [t["name"] for t in tools_resp.json()]
        assert "calculator" in tool_names
        assert "web_search" in tool_names

        # 2. Tool feasibility check
        feas_resp = await client.post("/api/tools/feasibility", json={
            "name": "custom_api",
            "tool_type": "http_request",
            "config": {"url": "https://api.github.com"},
        })
        assert feas_resp.status_code == 200
        assert feas_resp.json()["feasible"] is True

        # 3. Create Agent Config
        create_resp = await client.post("/api/agent-configs", json={
            "name": "SpecGen Agent",
            "system_prompt": "You generate technical specifications.",
            "planning_enabled": True,
        })
        assert create_resp.status_code == 200
        agent_data = create_resp.json()
        agent_id = agent_data["id"]

        # 4. Create thread & command
        thread_resp = await client.post("/api/threads", json={"agent_config_id": agent_id, "title": "Spec Task"})
        assert thread_resp.status_code == 200
        thread_id = thread_resp.json()["id"]

        cmd_resp = await client.post(f"/api/threads/{thread_id}/commands", json={
            "message": "Calculate 42 * 100",
            "agent_config_id": agent_id,
        })
        assert cmd_resp.status_code == 200
        assert "run_id" in cmd_resp.json()
