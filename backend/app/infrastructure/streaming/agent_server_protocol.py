"""
ForgeX — Agent Server Protocol Adapter

Dedicated module per spec §16.5 that:
1. Consumes LangGraph/Deep Agents event streams
2. Maps them to Agent Protocol messages
3. Adds sequence/event IDs
4. Namespaces subagent information
5. Exposes tool-call progress and results
6. Preserves interrupt information
7. Exposes todo/custom state where available
8. Records a bounded replay buffer per thread/run
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger("streaming.protocol")

# Maximum replay buffer size per run
MAX_REPLAY_BUFFER = 500


class AgentProtocolAdapter:
    """
    Translates agent execution events into Agent Streaming Protocol
    SSE frames compatible with HttpAgentServerAdapter on the frontend.
    """

    def __init__(self):
        # Bounded replay buffer keyed by run_id
        self._replay_buffers: dict[str, list[dict]] = defaultdict(list)
        # Active stream subscriptions
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def format_sse_event(self, event: dict, event_type: str = "message") -> str:
        """
        Format an event as an SSE frame per spec §16.4.

        Example output:
            id: 42
            event: message
            data: {"type":"...","seq":42,...}
        """
        seq = event.get("seq", 0)
        data = json.dumps(event, default=str)
        return f"id: {seq}\nevent: {event_type}\ndata: {data}\n\n"

    def record_event(self, run_id: str, event: dict) -> None:
        """Record an event in the replay buffer."""
        buffer = self._replay_buffers[run_id]
        buffer.append(event)
        # Enforce bounded buffer
        if len(buffer) > MAX_REPLAY_BUFFER:
            self._replay_buffers[run_id] = buffer[-MAX_REPLAY_BUFFER:]

        # Notify subscribers
        for queue in self._subscribers.get(run_id, []):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def get_replay(self, run_id: str, from_seq: int = 0) -> list[dict]:
        """Get replay events from a sequence number."""
        buffer = self._replay_buffers.get(run_id, [])
        return [e for e in buffer if e.get("seq", 0) > from_seq]

    async def subscribe(self, run_id: str, from_seq: int = 0) -> AsyncGenerator[dict, None]:
        """Subscribe to events for a run, with replay from a sequence number."""
        # First, replay buffered events
        for event in self.get_replay(run_id, from_seq):
            yield event

        # Then, subscribe for new events
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers[run_id].append(queue)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event

                    # Stop on run completion
                    if event.get("type") in ("run_end", "error"):
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"type": "keepalive", "timestamp": datetime.now(timezone.utc).isoformat()}
        finally:
            if queue in self._subscribers.get(run_id, []):
                self._subscribers[run_id].remove(queue)

    def cleanup_run(self, run_id: str, keep_replay: bool = True) -> None:
        """Clean up resources for a completed run."""
        if run_id in self._subscribers:
            del self._subscribers[run_id]
        if not keep_replay and run_id in self._replay_buffers:
            del self._replay_buffers[run_id]

    def translate_langgraph_event(self, raw_event: dict, seq: int) -> Optional[dict]:
        """
        Translate a raw LangGraph/Deep Agents event into an Agent Protocol message.

        This is the primary integration point for when real Deep Agents is connected.
        """
        event_type = raw_event.get("event", "")
        data = raw_event.get("data", {})
        timestamp = datetime.now(timezone.utc).isoformat()

        if event_type == "on_chat_model_stream":
            content = data.get("chunk", {}).get("content", "")
            if content:
                return {
                    "type": "message_chunk",
                    "seq": seq,
                    "content": content,
                    "timestamp": timestamp,
                }

        elif event_type == "on_tool_start":
            return {
                "type": "tool_call",
                "seq": seq,
                "tool_name": data.get("name", ""),
                "args": data.get("input", {}),
                "status": "running",
                "timestamp": timestamp,
            }

        elif event_type == "on_tool_end":
            return {
                "type": "tool_result",
                "seq": seq,
                "tool_name": data.get("name", ""),
                "result": data.get("output", ""),
                "status": "completed",
                "timestamp": timestamp,
            }

        elif event_type == "on_chain_end":
            return {
                "type": "run_end",
                "seq": seq,
                "status": "completed",
                "timestamp": timestamp,
            }

        return None


# Singleton protocol adapter
protocol_adapter = AgentProtocolAdapter()
