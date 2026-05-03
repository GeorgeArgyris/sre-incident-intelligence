import json
import random
import uuid
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

SERVICES = ["auth-service", "payment-gateway", "user-api", "notification-service", "inventory-service", "search-api", "recommendation-engine", "checkout-service"]
SEVERITIES = ["P1", "P2", "P3", "P4"]
ENVIRONMENTS = ["production", "staging", "production", "production"]  # weighted toward prod
ERROR_TYPES = ["latency_spike", "error_rate_increase", "memory_leak", "cpu_saturation", "db_connection_pool_exhausted", "timeout", "disk_full", "network_partition"]

def generate_incident():
    service = random.choice(SERVICES)
    severity = random.choice(SEVERITIES)
    error_type = random.choice(ERROR_TYPES)
    
    return {
        "incident_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "severity": severity,
        "environment": random.choice(ENVIRONMENTS),
        "error_type": error_type,
        "message": f"{service} experiencing {error_type.replace('_', ' ')}",
        "affected_users": random.randint(0, 50000),
        "region": random.choice(["us-east-1", "eu-west-1", "ap-southeast-1"]),
        "host": fake.hostname(),
        "duration_seconds": random.randint(30, 3600),
    }

if __name__ == "__main__":
    print(json.dumps(generate_incident(), indent=2))