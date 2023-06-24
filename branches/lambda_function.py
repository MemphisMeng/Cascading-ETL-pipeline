import json
import logging
from pythonjsonlogger import jsonlogger
from service import service, config

# Load environment
ENV = config.load_env()
 
LOGGER = logging.getLogger()
# Replace the LambdaLoggerHandler formatter :
LOGGER.handlers[0].setFormatter(jsonlogger.JsonFormatter())
# Set default logging level 
LOGGING_LEVEL = getattr(logging, ENV["app"]["LOGGING_LEVEL"])
LOGGER.setLevel(LOGGING_LEVEL)

def _lambda_context(context):
    """Extract information relevant from context object."""
    return {
        "function_name": context.function_name,
        "function_version": context.function_version
    }

# @datadog_lambda_wrapper
def lambda_handler(event, context):
    LOGGER.info("Starting lambda executing.", extra=_lambda_context(context))
    execution_summary = service.main(event, ENV)
    LOGGER.info("Successful lambda execution.", extra=_lambda_context(context))
    return {
        'statusCode': 200,
        'body': json.dumps(execution_summary)
    }
