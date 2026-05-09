import json
import os
import time
import random
from dotenv import load_dotenv
from confluent_kafka import Producer
from incident_factory import generate_incident

load_dotenv("../.env")

conf = {
    "bootstrap.servers": os.getenv("CONFLUENT_BOOTSTRAP_SERVERS"),
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "PLAIN",
    "sasl.username": os.getenv("CONFLUENT_API_KEY"),
    "sasl.password": os.getenv("CONFLUENT_API_SECRET"),
}

producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

if __name__ == "__main__":
    print("Starting producer...")

    while True:
        incident = generate_incident()
        producer.produce(
            topic="raw-incidents",
            key=incident["incident_id"],
            value=json.dumps(incident),
            callback=delivery_report,
        )
        producer.poll(0)
        sleep_time = random.uniform(1, 5)
        print(f"Sent: {incident['incident_id']} | {incident['service']} | {incident['severity']}")
        time.sleep(sleep_time)