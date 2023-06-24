import os
import sys
import logging

LOGGER = logging.getLogger(__name__)


def load_env():
    """Load enviroment variables."""
    try:
        return {
            "LOGGING_LEVEL": os.environ["LOGGING_LEVEL"],
            "APP_ENV": os.environ["APP_ENV"],
            "SOURCE_SQS": os.environ["SOURCE_SQS"],
            "TARGET_SQS": os.environ["TARGET_SQS"],
            "DB": os.environ["DB"],
        }
    except KeyError as error:
        LOGGER.exception("Enviroment variable %s is required.", error)
        sys.exit(1)
