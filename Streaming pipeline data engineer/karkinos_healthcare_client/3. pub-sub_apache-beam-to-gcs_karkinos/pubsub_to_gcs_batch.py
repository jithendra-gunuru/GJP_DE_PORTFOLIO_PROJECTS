import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from datetime import datetime
import json
import uuid

# ========== CONFIG SECTION ==========
PROJECT_ID = "gcp-de-vaarahi-b38"
REGION = "asia-south1"
BUCKET = "karkinos-health-client"
SUBSCRIPTION_NAME = "patient-events-sub"

INPUT_SUBSCRIPTION = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_NAME}"
OUTPUT_PATH = f"gs://{BUCKET}/dataflow/raw/patients/output"
STAGING_LOCATION = f"gs://{BUCKET}/dataflow/staging"
TEMP_LOCATION = f"gs://{BUCKET}/dataflow/temp"
RUNNER = "DataflowRunner"      # Use "DataflowRunner" on GCP Dataflow
STREAMING = True

# ========== PIPELINE OPTIONS ==========
options = PipelineOptions()
gcloud_options = options.view_as(GoogleCloudOptions)
gcloud_options.project = PROJECT_ID
gcloud_options.region = REGION
gcloud_options.staging_location = STAGING_LOCATION
gcloud_options.temp_location = TEMP_LOCATION

standard_options = options.view_as(StandardOptions)
standard_options.runner = RUNNER
standard_options.streaming = STREAMING
options.view_as(SetupOptions).save_main_session = True

# ========== CUSTOM DoFn ==========
class WriteBatchToGCS(beam.DoFn):
    """
    Writes a batch of messages into a GCS file in partitioned folders by time window.
    """
    def __init__(self, base_path):
        self.base_path = base_path

    def process(self, element, window=beam.DoFn.WindowParam):
        # element: (None, [messages])
        records = element[1]
        window_start = window.start.to_utc_datetime()
        gcs_path = (
            f"{self.base_path}/"
            f"{window_start.year:04}/{window_start.month:02}/{window_start.day:02}/"
            f"{window_start.hour:02}/{window_start.minute:02}/"
            f"batch-{window_start.strftime('%Y%m%d-%H%M')}-{uuid.uuid4().hex[:6]}.json"
        )
        from apache_beam.io.gcp.gcsio import GcsIO
        gcsio = GcsIO()
        # Write each message as a JSON line
        data = '\n'.join([json.dumps(json.loads(msg.decode('utf-8'))) for msg in records])
        with gcsio.open(gcs_path, 'w') as f:
            f.write(data.encode('utf-8'))
        yield gcs_path  # Optional: for logging/debug

# ========== MAIN PIPELINE ==========
def run():
    with beam.Pipeline(options=options) as p:
        (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(subscription=INPUT_SUBSCRIPTION)
            | 'WindowInto1Min' >> beam.WindowInto(beam.window.FixedWindows(60))
            | 'ToPair' >> beam.Map(lambda msg: (None, msg))
            | 'GroupByWindow' >> beam.GroupByKey()
            | 'WriteBatchToGCS' >> beam.ParDo(WriteBatchToGCS(OUTPUT_PATH))
        )

if __name__ == "__main__":
    run()
