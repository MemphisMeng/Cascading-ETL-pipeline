import logging, ast, requests, sys
from utils import *
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)


def main(event, environment):
    """
    Process the invoking event data and perform operations related to employees based on the input branch ID.

    Args:
        event (dict): A JSON-formatted document that contains data for a Lambda function to process.
        environment (dict): A context object that provides methods and properties about the invocation, function and runtime environment.

    Returns:
        None

    Raises:
        SystemExit: If an exception occurs during the execution.

    Notes:
        - The function retrieves messages from a source SQS queue and processes each message.
        - Each message is expected to contain a 'body' field that is evaluated as a dictionary using `ast.literal_eval`.
        - The function fetches employee information for a specified branch ID from a specified URL.
        - Only employees with the occupation of 'salesperson' are considered for updating the DynamoDB table.
        - The function checks if the employee record is already ingested into the table using the `ingestionCompleted` function.
        - If the employee record is not already ingested, it is updated in the table.
        - The function delivers a message containing the branch ID and employee ID to a target SQS queue for the next stage.
        - The function logs the successful sending of employees to the target queue and deletes processed messages from the source queue.
        - If an exception occurs during execution, the function logs the error and exits the program with a status code of 1.

    """
    LOGGER.info(event)

    source_sqs = environment["SOURCE_SQS"]
    target_sqs = environment["TARGET_SQS"]
    table = environment["DB"]

    messages = receive_message(source_sqs)

    for message in messages:
        try:
            message_body = message["body"]
            body = ast.literal_eval(message_body)
            branch_id = str(body["branch_id"])
            # go to a path that allows users to retrieve all information of the employees based on the input branch id
            response = requests.get(
                url=f"www.domain.com/employees?branchID={branch_id}"
            )
            response = response.json().get("result")

            if response:
                for employee in response.get("employees"):
                    if (
                        employee["occupation"] == "salesperson"
                    ):  # only looking for salespersons
                        if not ingestionCompleted(
                            table,
                            Key("employee_id").eq(str(employee["employee_id"])),
                            employee,
                            "employee_",
                        ):
                            # only update DynamoDB table when it's NOT complete ingesting
                            update_info(table, employee)
                        employee_id = str(employee["branch_id"])
                        workload = {"branch_id": branch_id, "employee_id": employee_id}
                        deliver_message(target_sqs, workload)
                        LOGGER.info(
                            f"Employee {employee_id} of branch {branch_id} is successfully sent to queue for the next stage!"
                        )
            delete_message(source_sqs, message["ReceiptHandle"])

        except Exception as e:
            LOGGER.error(str(e), exc_info=True)
            sys.exit(1)
