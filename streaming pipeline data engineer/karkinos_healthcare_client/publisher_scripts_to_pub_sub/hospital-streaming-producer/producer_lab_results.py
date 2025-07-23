import os
import requests
from google.cloud import pubsub_v1

from shared.config_util import load_config
from shared.fetch_api_key import get_api_key

# ---- Load Config ----
config = load_config()
API_URL = config['api']['lab_results_url']
PUBSUB_TOPIC = config['pubsub']['lab_results_topic']
API_KEY = get_api_key()

def fetch_lab_results():
    headers = {"x-api-key": API_KEY}
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()["lab_results"]

def publish_to_pubsub(lab_results):
    publisher = pubsub_v1.PublisherClient()
    import json
    for record in lab_results:
        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(PUBSUB_TOPIC, data=data)
        print("Published:", future.result())

if __name__ == "__main__":
    lab_results = fetch_lab_results()
    publish_to_pubsub(lab_results)
    print("✅ All lab results published to Pub/Sub.")
