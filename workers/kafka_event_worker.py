import json

from kafka import KafkaConsumer


consumer = KafkaConsumer(
    'crawler_events',
    bootstrap_servers='zlttbots-kafka:9092',
    auto_offset_reset='earliest',
    group_id='zlttbots-workers',
    value_deserializer=lambda message: json.loads(message.decode('utf-8')),
)

for message in consumer:
    event = message.value
    print('EVENT RECEIVED:', event)
