import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from datetime import datetime, timezone
import argparse
import json
import logging
import uuid

class AddGCSPathByTimestamp(beam.DoFn):
    def __init__(self, base_path):
        self.base_path = base_path.rstrip('/')

    def process(self, element, timestamp=beam.DoFn.TimestampParam):
        try:
            record = json.loads(element.decode('utf-8'))
            ts_str = record.get('event_timestamp')
            if ts_str:
                try:
                    event_time = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                except Exception:
                    event_time = datetime.fromtimestamp(float(ts_str) / 1000.0, tz=timezone.utc)
            else:
                event_time = datetime.utcfromtimestamp(float(timestamp))
        except Exception:
            event_time = datetime.utcfromtimestamp(float(timestamp))
        gcs_prefix = f"{self.base_path}/{event_time.year:04}/{event_time.month:02}/{event_time.day:02}/{event_time.hour:02}"
        yield (gcs_prefix, element)

class WriteToGCSDoFn(beam.DoFn):
    def process(self, element):
        prefix, message = element
        from apache_beam.io.gcp.gcsio import GcsIO
        filename = f"{prefix}/message-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.json"
        gcsio = GcsIO()
        gcsio.open(filename, mode='w').write((message.decode('utf-8') + '\n').encode('utf-8'))
        logging.info(f"Wrote message to {filename}")

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--input_subscription', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--staging_location', required=True)
    parser.add_argument('--temp_location', required=True)
    parser.add_argument('--runner', default='DataflowRunner')
    args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    gcloud_options = options.view_as(GoogleCloudOptions)
    gcloud_options.project = args.project
    gcloud_options.region = args.region
    gcloud_options.staging_location = args.staging_location
    gcloud_options.temp_location = args.temp_location
    standard_options = options.view_as(StandardOptions)
    standard_options.runner = args.runner
    standard_options.streaming = True
    options.view_as(SetupOptions).save_main_session = True

    logging.getLogger().setLevel(logging.INFO)

    with beam.Pipeline(options=options) as p:
        (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(subscription=args.input_subscription)
            | 'AddGCSPath' >> beam.ParDo(AddGCSPathByTimestamp(args.output_path))
            | 'WriteToGCS' >> beam.ParDo(WriteToGCSDoFn())
        )

if __name__ == '__main__':
    run()
