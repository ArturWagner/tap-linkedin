#!/usr/bin/env python3
import os
import json
import singer
from singer import utils, metadata, Transformer
from datetime import datetime
from tap_linkedin import linkedin

REQUIRED_CONFIG_KEYS = ["access_token", "account_id", "start_date", "end_date"]
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


# Load schemas from schemas folder
def load_schemas():
    schemas = {}

    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = json.load(file)

    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []

    for schema_name, schema in raw_schemas.items():
        # create and add catalog entry
        catalog_entry = {
            'stream': schema_name,
            'tap_stream_id': schema_name,
            'schema': schema,
            'metadata': [],
            'key_properties': []
        }
        streams.append(catalog_entry)

    return {'streams': streams}


def get_selected_streams(catalog):
    '''
    Gets selected streams.  Checks schema's 'selected' first (legacy)
    and then checks metadata (current), looking for an empty breadcrumb
    and mdata with a 'selected' entry
    '''
    selected_streams = []
    for stream in catalog.streams:
        stream_metadata = metadata.to_map(stream.metadata)
        # stream metadata will have an empty breadcrumb
        if metadata.get(stream_metadata, (), "selected"):
            selected_streams.append(stream.tap_stream_id)

    return selected_streams


def get_metrics_from_schema(stream):
    # only flat metrics for now
    schema_dict = stream.schema.to_dict()
    metadata_dict = metadata.to_map(stream.metadata)

    def is_metric(prop):
        return metadata.get(
            metadata_dict,
            ("properties", prop),
            "dimension") is not True and prop != "date"

    metrics = [prop for prop in schema_dict['properties'] if is_metric(prop)]
    LOGGER.info('Getting Metrics')
    LOGGER.info(metrics)
    return metrics


def sync(config, state, catalog):

    selected_stream_ids = get_selected_streams(catalog)
    # Loop over streams in catalog
    for stream in catalog.streams:
        stream_id = stream.tap_stream_id
        stream_schema = stream.schema
        stream_alias = stream.stream_alias
        if stream_id in selected_stream_ids:
            # TODO: sync code for stream goes here...
            campaigns = linkedin.get_campaigns(config)
            singer_lines = {}
            for campaign in campaigns:
                lines = campaign
                metric_line = lines

                with Transformer(
                        singer.UNIX_MILLISECONDS_INTEGER_DATETIME_PARSING
                        ) as bumble_bee:
                    singer_line = bumble_bee.transform(
                        metric_line, stream_schema.to_dict()
                    )

                singer_lines.update(singer_line)
                singer.write_schema(
                    stream_id,
                    stream_schema.to_dict(),
                    "date",
                    None,
                    stream.stream_alias
                )

                today = datetime.now().date().isoformat()
                singer_lines['date_extraction'] = today
                singer.write_record(stream_id, singer_lines, stream_alias)

    return


def build_singer_line(line):
    singer_line = {}
    field_name = line['name']
    singer_line[field_name] = line['values'][0]['value']

    return singer_line


@utils.handle_top_exception(LOGGER)
def main():

    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        print(json.dumps(catalog, indent=2))
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()

        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
