import json

from kafka import KafkaProducer


class KafkaEventProducer:
    def __init__(self, broker: str = 'zttato-kafka:9092') -> None:
        self.producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda value: json.dumps(value).encode('utf-8'),
        )

    def publish(self, topic: str, payload: dict) -> None:
        self.producer.send(topic, payload)
        self.producer.flush()
