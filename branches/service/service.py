import logging, requests, sys
from utils import *
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)


def main(event, environment):
    """Process invoking event data and update the DynamoDB table based on specified branches.

    Args:
        event (dict): A JSON-formatted document that contains data for a Lambda function to process.
        environment (dict): A context object that provides methods and properties about the invocation, function and runtime environment.

    Returns:
        None

    Raises:
        SystemExit: If an exception occurs during the execution.

    Notes:
        - If `event` does not contain the 'branches' key, the function will default to processing information for all branches.
        - The function retrieves branch-specific information from a URL and updates the DynamoDB table accordingly.
        - The updated information is then delivered to an SQS queue for further processing.

    """
    LOGGER.info(event)

    if not event.get("branches"):
        # default to look up all branches if the value is an empty list
        branches = [
            "Scranton",
            "Akron",
            "Buffalo",
            "Rochester",
            "Syracuse",
            "Utica",
            "Binghamton",
            "Albany",
            "Nashua",
            "Pittsfield",
            "Stamford",
            "Yonkers",
            "New York",
        ]
    else:
        branches = event["branches"]  # should be an array

    queue = environment["SQS"]
    table = environment["DB"]

    try:
        for branch in branches:
            # go to a path that allows users to retrieve all information of the specified branch(es) based on input date range
            response = requests.get(
                url=f"www.dundermifflinpaper.com/branches/?branch={branch}"
            )
            response = response.json()
            branches = response.get("result")
            for result in branches:
                if not upToDate(
                    table,
                    Key("branch_id").eq(str(result["id"])),
                    result,
                    "branch_",
                ):
                    # only update DynamoDB table when it's NOT complete ingesting
                    update_info(table, result)

            deliver_message(queue, str({"branch": result["branch_id"]}))
            LOGGER.info(f"sending branch {result['branch_id']} for the next stage")

    except Exception as e:
        LOGGER.error(str(e), exc_info=True)
        sys.exit(1)
