# sender.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

test_data = {
    "message": "Hello from Kafka!",
    "number": 123
}

producer.send('test_topic', value=test_data)
producer.flush()

print("✅ Test message sent.")
