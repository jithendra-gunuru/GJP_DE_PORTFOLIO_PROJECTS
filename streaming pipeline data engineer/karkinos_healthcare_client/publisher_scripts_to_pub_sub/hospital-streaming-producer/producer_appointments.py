import os
import requests
from google.cloud import pubsub_v1

from shared.config_util import load_config
from shared.fetch_api_key import get_api_key

# ---- Load Config ----
config = load_config()
API_URL = config['api']['appointments_url']
PUBSUB_TOPIC = config['pubsub']['appointments_topic']
API_KEY = get_api_key()

def fetch_appointments():
    headers = {"x-api-key": API_KEY}
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()["appointments"]

def publish_to_pubsub(appointments):
    publisher = pubsub_v1.PublisherClient()
    import json
    for record in appointments:
        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(PUBSUB_TOPIC, data=data)
        print("Published:", future.result())

if __name__ == "__main__":
    appointments = fetch_appointments()
    publish_to_pubsub(appointments)
    print("✅ All appointments published to Pub/Sub.")
