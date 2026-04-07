from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Iterable, Protocol


@dataclass(frozen=True)
class Event:
    topic: str
    payload: dict[str, Any]


class EventBus:
    """Simple in-memory event bus with deterministic FIFO ordering."""

    def __init__(self) -> None:
        self._queue: Deque[Event] = deque()
        self._history: list[Event] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        if not topic:
            raise ValueError("topic must be non-empty")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        event = Event(topic=topic, payload=payload)
        self._queue.append(event)
        self._history.append(event)

    def consume(self) -> Iterable[Event]:
        while self._queue:
            yield self._queue.popleft()

    def history(self) -> list[Event]:
        return list(self._history)


class Agent(Protocol):
    subscriptions: tuple[str, ...]

    def handle(self, topic: str, payload: dict[str, Any], bus: EventBus) -> None: ...


class Orchestrator:
    def __init__(self, agents: list[Agent], bus: EventBus) -> None:
        self._agents = agents
        self._bus = bus

    def dispatch(self, topic: str, payload: dict[str, Any]) -> None:
        for agent in self._agents:
            if topic in agent.subscriptions:
                agent.handle(topic=topic, payload=payload, bus=self._bus)

    def run(self) -> None:
        for event in self._bus.consume():
            self.dispatch(topic=event.topic, payload=event.payload)
