import logging, requests, boto3, sys
from utils import reserved_words
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)

def main(event, environment):
    """_summary_

    Args:
        event (dict): incoming data dict to be processed
        environment (dict): _description_
    """    
    LOGGER.info(event)

    if not event.get('start_date'):
        # default to start from 3 days earlier
        start_date = datetime.strftime(datetime.utcnow() - timedelta(days = 3), "%Y-%m-%d")
    else:
        start_date = event['start_date']
    if not event.get('end_date'):
        # default to end on the current day
        end_date = datetime.strftime(datetime.utcnow(), "%Y-%m-%d")
    else:
        end_date = event['end_date']

    queue = environment['SQS']
    table = environment['DB']

    try:
        query = {
            'startdate': start_date,
            'enddate': end_date
        }
        # go to a path that allows users to retrieve events based on input date range
        response = requests.get(
            url='www.domain.com/Events/GetEventListFromDateRange',
            params=query
        )
        response = response.json()
        for result in response.get('result'):
            if eventExisted(table, Key('event_id').eq(str(result['event_id'])), result):
                update_event_info(table, result)

        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl=queue,
            MessageBody=(
                str({'event': result['event_id']})
            ),          
        )
        LOGGER.info(f"sending event {result['event_id']} for the next stage")

    except Exception as e:
        LOGGER.error(str(e), exc_info=True)
        sys.exit(1)

def eventExisted(table_name, condition, result):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    retrieval = table.query(KeyConditionExpression=condition)['Items']

    existing_items = 0
    if len(retrieval) > 0:
        for key in retrieval.keys():
            if key.upper() not in reserved_words:
                if result[key] == retrieval[0].get(key):
                    existing_items += 1
            elif result['key'] == retrieval[0].get('event_' + key):
                existing_items += 1

            LOGGER.info(f"key:{key}| existing_items:{existing_items}")
    event_ingested_flag = len(retrieval) and existing_items == len(result.items()) - 1
    return event_ingested_flag

def update_event_info(table_name, record):
    event_id = str(record['event_id'])
    
    event_record = {}
    for k, v in record.items():
        if k not in ['event_id', 'players']:
            if k.upper() not in reserved_words:
                event_record[k] = v
            else:
                event_record['event_' + k] = v

    event_record['last_modified'] = str(datetime.utcnow())
    LOGGER.info(f'To update: {event_record}')
    update_table(table_name, {'event_id': event_id}, event_record)
              