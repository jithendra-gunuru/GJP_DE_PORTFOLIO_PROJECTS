import os
import requests
from google.cloud import pubsub_v1

from shared.config_util import load_config
from shared.fetch_api_key import get_api_key

# ---- Load Config ----
config = load_config()
API_URL = config['api']['patients_url']
PUBSUB_TOPIC = config['pubsub']['patients_topic']
API_KEY = get_api_key()

def fetch_patients():
    headers = {"x-api-key": API_KEY}
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()["patients"]

def publish_to_pubsub(patients):
    publisher = pubsub_v1.PublisherClient()
    for record in patients:
        # Convert dict to JSON string, then bytes
        import json
        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(PUBSUB_TOPIC, data=data)
        print("Published: ", future.result())

if __name__ == "__main__":
    patients = fetch_patients()
    publish_to_pubsub(patients)
    print("✅ All patients published to Pub/Sub.")
