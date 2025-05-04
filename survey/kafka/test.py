# send_test_message.py

import json
from kafka import KafkaProducer

# Настройка продюсера Kafka
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Пример тестового сообщения
test_message = {
    "employee_uuid": "123e4567-e89b-12d3-a456-426614174000",  # замените на реальный UUID сотрудника
    "topic": "Охрана труда",  # замените на существующую тему
    "exam_type": "Проверка знаний",  # замените на существующий тип
    "date_passed": "2025-05-04",
    "score": 88,
    "station_name": "Центральная станция"  # замените на существующее подразделение
}

# Отправка сообщения
producer.send('exam_results', value=test_message)
producer.flush()

print("✅ Test message sent.")
