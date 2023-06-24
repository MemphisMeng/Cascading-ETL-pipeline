import logging, ast, requests, sys
from utils import *
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)


def main(event, environment):
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
