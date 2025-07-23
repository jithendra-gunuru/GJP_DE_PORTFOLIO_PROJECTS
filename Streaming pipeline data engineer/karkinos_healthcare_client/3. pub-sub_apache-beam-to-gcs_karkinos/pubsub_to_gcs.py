"""
Apache Beam pipeline to read from Pub/Sub subscription `patient-events-sub`
in GCP project `gcp-de-vaarahi-b38` and write messages to partitioned GCS folder structure.

Subscription: projects/gcp-de-vaarahi-b38/subscriptions/patient-events-sub
Project ID:  gcp-de-vaarahi-b38
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from datetime import datetime, timezone
import json
import logging
import uuid

# ================== HARD-CODED CONFIG ==================
PROJECT_ID = "gcp-de-vaarahi-b38"
REGION = "asia-south1"
BUCKET = "karkinos-health-client"
SUBSCRIPTION_NAME = "patient-events-sub"
INPUT_SUBSCRIPTION = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_NAME}"
OUTPUT_PATH = f"gs://{BUCKET}/dataflow/raw/patients/output"
STAGING_LOCATION = f"gs://{BUCKET}/dataflow/staging"
TEMP_LOCATION = f"gs://{BUCKET}/dataflow/temp"
RUNNER = "DataflowRunner"

# ========== Dofn to Attach GCS Path By Timestamp ==========
class AddGCSPathByTimestamp(beam.DoFn):
    """
    Attaches a GCS path prefix based on the message's event timestamp (or processing time).
    Output: (gcs_prefix, message_str)
    """
    def __init__(self, base_path):
        self.base_path = base_path.rstrip('/')

    def process(self, element, timestamp=beam.DoFn.TimestampParam):
        try:
            record = json.loads(element)
            ts_str = record.get('event_timestamp')
            if ts_str:
                try:
                    # Try ISO8601
                    event_time = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                except Exception:
                    # Try epoch millis
                    event_time = datetime.fromtimestamp(float(ts_str) / 1000.0, tz=timezone.utc)
            else:
                # Use processing time if missing
                event_time = datetime.utcfromtimestamp(float(timestamp))
        except Exception:
            event_time = datetime.utcfromtimestamp(float(timestamp))

        gcs_prefix = f"{self.base_path}/{event_time.year:04}/{event_time.month:02}/{event_time.day:02}/{event_time.hour:02}"
        yield (gcs_prefix, element)

# ========== Dofn to Write To GCS ==========
class WriteToGCSDoFn(beam.DoFn):
    """Write each message as a line to a GCS file under the computed prefix."""
    def process(self, element):
        prefix, message = element
        from apache_beam.io.gcp.gcsio import GcsIO
        filename = f"{prefix}/message-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.json"
        gcsio = GcsIO()
        with gcsio.open(filename, mode='w') as f:
            f.write((message + '\n').encode('utf-8'))
        logging.info(f"Wrote message to {filename}")

# ========== MAIN PIPELINE ==========
def run():
    options = PipelineOptions()
    gcloud_options = options.view_as(GoogleCloudOptions)
    gcloud_options.project = PROJECT_ID
    gcloud_options.region = REGION
    gcloud_options.staging_location = STAGING_LOCATION
    gcloud_options.temp_location = TEMP_LOCATION

    standard_options = options.view_as(StandardOptions)
    standard_options.runner = RUNNER
    standard_options.streaming = True
    options.view_as(SetupOptions).save_main_session = True

    logging.getLogger().setLevel(logging.INFO)

    with beam.Pipeline(options=options) as p:
        messages = (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(subscription=INPUT_SUBSCRIPTION)
            | 'DecodeBytes' >> beam.Map(lambda x: x.decode('utf-8'))
        )
        partitioned = (
            messages
            | 'AttachGCSPath' >> beam.ParDo(AddGCSPathByTimestamp(OUTPUT_PATH))
        )
        _ = (
            partitioned
            | 'WriteToGCS' >> beam.ParDo(WriteToGCSDoFn())
        )

if __name__ == '__main__':
    run()
