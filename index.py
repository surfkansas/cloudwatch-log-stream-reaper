import datetime
import json
import time

import boto3

def log_info(message, **kwargs):
    log_message = {
        'level': 'INFO', 
        'message': message,
        **kwargs
    }
    print(json.dumps(log_message))

def lambda_handler(event, context):

    log_info('Beggining empty expired log stream purge')

    client = boto3.client('logs')
    
    delete_count = 0

    for log_group in get_log_groups(client):
        for expired_log_stream in get_expired_log_streams(client, log_group):
            delete_log_stream(client, log_group, expired_log_stream)
            delete_count += 1
            if delete_count % 5 == 0:
                # Prevents the log stream delete throttle (5 per second) from blocking execution.
                time.sleep(1)
                delete_count = 0

    log_info('Completed empty expired log stream purge', delete_count = delete_count)

def get_log_groups(client):

    paginator = client.get_paginator('describe_log_groups')

    response_iterator = paginator.paginate()

    for response_item in response_iterator:
        for log_group_item in response_item.get('logGroups', []):
            if 'retentionInDays' in log_group_item:
                yield log_group_item

def get_expired_log_streams(client, log_group):

    log_group_name = log_group['logGroupName']
    retention_in_days = log_group['retentionInDays']

    cutoff_date = datetime.datetime.utcnow() -  datetime.timedelta(days = retention_in_days + 2)

    log_info('Processing log group', log_group_name = log_group_name, retention_in_days = retention_in_days, cutoff_date = str(cutoff_date))

    paginator = client.get_paginator('describe_log_streams')

    response_iterator = paginator.paginate(
        logGroupName = log_group_name,
        orderBy = 'LastEventTime',
        descending = False
    )

    for reposonse_item in response_iterator:
        for log_stream_item in reposonse_item.get('logStreams'):
            log_stream_name = log_stream_item['logStreamName']
            if 'lastEventTimestamp' in log_stream_item and 'lastIngestionTime' in log_stream_item:
                last_event_timestamp = datetime.datetime.fromtimestamp(log_stream_item['lastEventTimestamp'] / 1000)
                last_event_ingestion_timestamp = datetime.datetime.fromtimestamp(log_stream_item['lastIngestionTime'] / 1000)
                if last_event_timestamp < cutoff_date and last_event_ingestion_timestamp < cutoff_date:
                    log_events = client.get_log_events(
                        logGroupName = log_group_name,
                        logStreamName = log_stream_name,
                        startFromHead = True,
                        limit = 1
                    )
                    if len(log_events.get('events', [])) == 0:
                        log_info('Identified log stream to delete', log_group_name = log_group_name, log_stream_name = log_stream_name, \
                            retention_in_days = retention_in_days, cutoff_date = str(cutoff_date), \
                            last_event_timestamp = str(last_event_timestamp), last_event_ingestion_timestamp = str(last_event_ingestion_timestamp), \
                            log_event_count = 0 )
                        yield log_stream_item
        

def delete_log_stream(client, log_group, expired_log_stream):
    client.delete_log_stream(
        logGroupName = log_group['logGroupName'],
        logStreamName = expired_log_stream['logStreamName']
    )