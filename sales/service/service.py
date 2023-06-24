import logging, ast, requests, sys
from utils import *
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)

def main(event, environment):

    LOGGER.info(event)

    source_sqs = environment['SOURCE_SQS']
    table = environment['DB']

    messages = receive_message(source_sqs)
    for message in messages:
        try:
            message_body = message['Body']
            body = ast.literal_eval(message_body)
            employee_id = str(body["employee_id"])
            branch_id = str(body['branch_id'])
            # go to a path that allows users to retrieve all information of the sales given that the salesperson ID is provided
            response = requests.get(
                url=f"www.domain.com/sales/?salespersonsID={employee_id}"
            )
            sales = response.json().get("result") # all the sales records of this salesperson
            now = datetime.utcnow() # the unix timestamp of the current time in UTC
            for sale in sales:
                sale_timestamp = datetime.strptime(sale['transaction_timestamp'], '%Y-%m-%d %H:%M:%S')
                if now - timedelta(hours=24) <= sale_timestamp and sale_timestamp < now: # only look for the transactions made within the last 24 hrs
                    if not ingestionCompleted(
                        table,
                        Key("sale_id").eq(str(sale["id"])),
                        sale,
                        "sale_",
                    ):
                        # only update DynamoDB table when it's NOT complete ingesting
                        sale['branch_id'] = branch_id # append branch info to the sale payload
                        update_info(table, sale)
                        LOGGER.info(f"Successfully ingested the sale record {sale['id']} into our database!")
            delete_message(source_sqs, message['ReceiptHandle'])

        except Exception as e:
            LOGGER.error(str(e), exc_info=True)
            sys.exit(1)
