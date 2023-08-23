import logging, ast, requests, sys
from utils import *
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)


def main(event, environment):
    """
    Process the invoking event data and update the DynamoDB table with relevant sales information.

    Args:
        event (dict): A JSON-formatted document that contains data for a Lambda function to process.
        environment (dict): A context object that provides methods and properties about the invocation, function and runtime environment.

    Returns:
        None

    Raises:
        SystemExit: If an exception occurs during the execution.

    Notes:
        - The function retrieves messages from an SQS queue and processes each message.
        - Each message is expected to contain a 'Body' field that is evaluated as a dictionary using `ast.literal_eval`.
        - The function fetches sales information for a specified employee ID from a specified URL.
        - Only sales transactions made within the last 24 hours are considered for updating the DynamoDB table.
        - The function checks if the sale record is already ingested into the table using the `ingestionCompleted` function.
        - If the sale record is not already ingested, it is updated in the table along with the branch ID.
        - The function logs successful ingestion of sale records and deletes processed messages from the SQS queue.
        - If an exception occurs during execution, the function logs the error and exits the program with a status code of 1.

    """
    LOGGER.info(event)

    sqs = environment["SQS"]
    table = environment["DB"]

    messages = receive_message(sqs)
    for message in messages:
        try:
            message_body = message["Body"]
            body = ast.literal_eval(message_body)
            employee_id = str(body["employee_id"])
            branch_id = str(body["branch_id"]) + 'c'
            # go to a path that allows users to retrieve all information of the sales given that the salesperson ID is provided
            response = requests.get(
                url=f"www.dundermifflinpaper.com/sales/?salespersonsID={employee_id}"
            )
            sales = (
                response.json().get("result").get("sales")
            )  # all the sales records of this salesperson
            now = datetime.utcnow()  # the unix timestamp of the current time in UTC
            for sale in sales:
                sale_timestamp = datetime.strptime(
                    sale["transaction_timestamp"], "%Y-%m-%d %H:%M:%S"
                )
                if (
                    now - timedelta(hours=24) <= sale_timestamp and sale_timestamp < now
                ):  # only look for the transactions made within the last 24 hrs
                    if not upToDate(
                        table,
                        Key("sale_id").eq(str(sale["id"])),
                        sale,
                        "sale_",
                    ):
                        # only update DynamoDB table when it's NOT complete ingesting
                        sale[
                            "branch_id"
                        ] = branch_id  # append branch info to the sale payload
                        update_info(table, sale)
                        LOGGER.info(
                            f"Successfully ingested the sale record {sale['id']} into our database!"
                        )
            delete_message(sqs, message["ReceiptHandle"])

        except Exception as e:
            LOGGER.error(str(e), exc_info=True)
            sys.exit(1)
