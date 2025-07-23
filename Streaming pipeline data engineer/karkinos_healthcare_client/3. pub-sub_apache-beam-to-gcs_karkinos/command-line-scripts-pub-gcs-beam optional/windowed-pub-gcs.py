import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from datetime import datetime, timezone
import argparse
import json
import logging
import uuid

class WriteBatchToGCS(beam.DoFn):
    def __init__(self, base_path):
        self.base_path = base_path.rstrip('/')

    def process(self, element, window=beam.DoFn.WindowParam):
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
        data = '\n'.join([json.dumps(json.loads(msg.decode('utf-8'))) for msg in records])
        with gcsio.open(gcs_path, 'w') as f:
            f.write(data.encode('utf-8'))
        yield gcs_path

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--input_subscription', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--staging_location', required=True)
    parser.add_argument('--temp_location', required=True)
    parser.add_argument('--window_size', default=60, type=int, help='Window size in seconds')
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
            | 'WindowInto' >> beam.WindowInto(beam.window.FixedWindows(args.window_size))
            | 'ToPair' >> beam.Map(lambda msg: (None, msg))
            | 'GroupByWindow' >> beam.GroupByKey()
            | 'WriteBatchToGCS' >> beam.ParDo(WriteBatchToGCS(args.output_path))
        )

if __name__ == '__main__':
    run()
