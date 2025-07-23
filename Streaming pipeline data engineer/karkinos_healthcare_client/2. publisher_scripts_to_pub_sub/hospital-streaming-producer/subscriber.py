from google.cloud import pubsub_v1

# Replace with your values
PROJECT_ID = "gcp-de-vaarahi-b38"
SUBSCRIPTION_ID = "patient-events-sub"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"

def callback(message):
    print(f"Received message: {message.data.decode('utf-8')}")
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print("Listening for messages...")

try:
    streaming_pull_future.result(timeout=60)  # Listen for 60 seconds (increase as needed)
except Exception as e:
    streaming_pull_future.cancel()
