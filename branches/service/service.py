import logging, requests, sys
from utils import *
from boto3.dynamodb.conditions import Key

LOGGER = logging.getLogger(__name__)


def main(event, environment):
    """_summary_

    Args:
        event (dict): incoming data dict to be processed
        environment (dict): _description_
    """
    LOGGER.info(event)

    if not event.get("branches"):
        # default to look up all branches
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
            response = requests.get(url=f"www.domain.com/branches/?branch={branch}")
            response = response.json()
            for result in response.get("result"):
                if not ingestionCompleted(
                    table,
                    Key("branch_id").eq(str(result["branch_id"])),
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
