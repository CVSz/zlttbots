from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class QueueMessage:
    topic: str
    payload: dict[str, object]
    headers: dict[str, str] = field(default_factory=dict)


class CentralQueue:
    """Topic queue abstraction representing a central event backbone."""

    def __init__(self) -> None:
        self._topics: dict[str, deque[QueueMessage]] = defaultdict(deque)

    def publish(self, message: QueueMessage) -> None:
        self._topics[message.topic].append(message)

    def consume(self, topic: str, batch_size: int = 1) -> list[QueueMessage]:
        messages: list[QueueMessage] = []
        topic_queue = self._topics[topic]
        for _ in range(min(batch_size, len(topic_queue))):
            messages.append(topic_queue.popleft())
        return messages

    def depth(self, topic: str) -> int:
        return len(self._topics[topic])

    def topics(self) -> tuple[str, ...]:
        return tuple(sorted(self._topics.keys()))
