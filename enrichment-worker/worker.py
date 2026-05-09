import json
import os
from dotenv import load_dotenv
from confluent_kafka import Consumer, Producer
from enricher import enrich_incident
from db import run_migration, save_incident

load_dotenv("../.env")

base_conf = {
    "bootstrap.servers": os.getenv("CONFLUENT_BOOTSTRAP_SERVERS") or "localhost:9092"
}
if os.getenv("CONFLUENT_API_KEY"):
    base_conf.update({
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "PLAIN",
        "sasl.username": os.getenv("CONFLUENT_API_KEY"),
        "sasl.password": os.getenv("CONFLUENT_API_SECRET"),
    })

consumer_conf = base_conf.copy()
consumer_conf.update({
    "group.id": "enrichment-worker-group",
    "auto.offset.reset": "earliest",
})

consumer = Consumer(consumer_conf)
dlq_producer = Producer(base_conf)

def send_to_dlq(raw: str, reason: str):
    dlq_producer.produce(
        topic="dead-letter-queue",
        value=json.dumps({"raw": raw, "reason": reason}),
    )
    dlq_producer.poll(0)
    print(f"Sent to DLQ: {reason}")

if __name__ == "__main__":
    print("Running migration...")
    run_migration()

    print("Starting enrichment worker...")
    consumer.subscribe(["raw-incidents"])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            raw = msg.value().decode("utf-8")
            print(f"Received: {raw[:80]}...")

            try:
                incident = json.loads(raw)
                enriched = enrich_incident(incident)
                save_incident(enriched)
                print(f"Saved: {enriched.incident_id} | {enriched.service} | {enriched.severity}")
            except Exception as e:
                print(f"Error enriching: {e}")
                send_to_dlq(raw, str(e))

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()