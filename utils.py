import boto3, logging
from datetime import datetime

LOGGER = logging.getLogger(__name__)

# boto3 setup
session = boto3.session.Session()
dynamodb = session.resource("dynamodb")
sqs = session.client("sqs")


def update_table(table_name, key, record):
    """
    Update the specified DynamoDB table with the provided record.

    Args:
        table_name (str): The name of the DynamoDB table to update.
        key (dict): The key identifying the record to update.
        record (dict): The updated values to set for the record.

    Returns:
        None

    Notes:
        - The function constructs an update expression and expression attribute values for each key-value pair in the record.
        - It uses the provided table name and key to access the DynamoDB table.
        - The function updates the item in the table using the constructed update expression and expression attribute values.
        - The function logs the successful completion of the update operation, including the affected table and key.
        - If an error occurs during the update operation, it is logged, and the function returns without raising an exception.

    """
    try:
        update_expression = ["set "]
        update_values = dict()
        for k, v in record.items():
            update_expression.append(f" {k} = :{k},")
            update_values[f":{k}"] = v

        table = dynamodb.Table(table_name)
        r = table.update_item(
            Key=key,
            UpdateExpression="".join(update_expression)[:-1],
            ExpressionAttributeValues=update_values,
        )

        info = f"""successfully completed the update operation of item: {list(key.values())[0]} to table {table_name}"""
        LOGGER.info(info, extra=r)
        return

    except Exception as e:
        LOGGER.info(e)
        return


def ingestionCompleted(table_name, condition, result, prefix):
    """
    Check if the ingestion of a record into the specified DynamoDB table is completed.

    Args:
        table_name (str): The name of the DynamoDB table to check.
        condition (boto3.dynamodb.conditions.Key): The key condition expression for querying the table.
        result (dict): The record to check for ingestion completion.
        prefix (str): The prefix used for key matching.

    Returns:
        bool: True if the ingestion is completed, False otherwise.

    Notes:
        - The function queries the specified DynamoDB table using the provided condition.
        - It retrieves the items matching the condition.
        - The function compares the key-value pairs of the result with the retrieved items, accounting for the provided prefix if applicable.
        - If all key-value pairs match between the result and the retrieved items, the ingestion is considered completed.
        - The function returns True if the ingestion is completed, and False otherwise.

    """
    table = dynamodb.Table(table_name)
    retrieval = table.query(KeyConditionExpression=condition)["Items"]

    existing_items = 0
    if len(retrieval) > 0:
        for key in retrieval.keys():
            if key.upper() not in reserved_words:
                if result[key] == retrieval[0].get(key):
                    existing_items += 1
            elif result["key"] == retrieval[0].get(prefix + key):
                existing_items += 1

    completed = len(retrieval) and existing_items == len(result.items())
    # len(retrieval) == 0: the item doesn't exist in DynamoDB at all
    # existing_items == len(result.items()): the item exists and all its key-value pairs
    # are synced up with API
    return completed


def update_info(table_name, record, primary_key, prefix):
    """
    Update the specified DynamoDB table with the given record.

    Args:
        table_name (str): The name of the DynamoDB table to update.
        record (dict): The record to update in the table.
        primary_key (str): The primary key of the record.
        prefix (str): The prefix used for key matching.

    Returns:
        None

    Notes:
        - The function constructs a new dictionary `to_insert_record` by iterating over the key-value pairs of the input `record`.
        - The primary key is excluded from `to_insert_record`.
        - If a key is not a reserved word, it is added to `to_insert_record` as is.
        - If a key is a reserved word, it is added to `to_insert_record` with the specified prefix.
        - The `last_modified` field is added to `to_insert_record` with the current UTC timestamp.
        - The function logs the update operation and calls the `update_table` function to perform the update.

    """
    item_id = str(record[primary_key])

    to_insert_record = {}
    for k, v in record.items():
        if k != primary_key:
            if k.upper() not in reserved_words:
                to_insert_record[k] = v
            else:
                to_insert_record[prefix + k] = v

    to_insert_record["last_modified"] = str(datetime.utcnow())
    LOGGER.info(f"To update: {to_insert_record}")
    update_table(table_name, {primary_key: item_id}, to_insert_record)


def deliver_message(queue_url, message):
    """
    Deliver a message to the specified queue URL.

    Args:
        queue_url (str): The URL of the queue to deliver the message to.
        message (Any): The message to be delivered.

    Returns:
        None

    Notes:
        - The function uses the `sqs` object to send a message to the specified `queue_url`.
        - The message body is converted to a string before delivery.

    """
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=(str(message)),
    )


def delete_message(url, ReceiptHandle):
    """
    Delete a message from the specified queue.

    Args:
        url (str): The URL of the queue.
        ReceiptHandle (str): The receipt handle of the message to delete.

    Returns:
        None

    Notes:
        - The function uses the `sqs` object to delete a message from the specified `url` using the provided `ReceiptHandle`.

    """
    sqs.delete_message(QueueUrl=url, ReceiptHandle=ReceiptHandle)


def receive_message(url, maxNumberOfMessages=10):
    """
    Receive messages from the specified queue URL.

    Args:
        url (str): The URL of the queue to receive messages from.
        maxNumberOfMessages (int): The maximum number of messages to receive (default: 10).

    Returns:
        List[dict]: A list of received messages.

    Notes:
        - The function uses the `sqs` object to receive messages from the specified `url` with the provided `maxNumberOfMessages`.
        - The received messages are extracted from the response and returned as a list.

    """
    response = sqs.receive_message(
        QueueUrl=url, MaxNumberOfMessages=maxNumberOfMessages, VisibilityTimeout=120
    )
    result = response.get("Messages", [])
    return result


reserved_words = [
    "ABORT",
    "ABSOLUTE",
    "ACTION",
    "ADD",
    "AFTER",
    "AGENT",
    "AGGREGATE",
    "ALL",
    "ALLOCATE",
    "ALTER",
    "ANALYZE",
    "AND",
    "ANY",
    "ARCHIVE",
    "ARE",
    "ARRAY",
    "AS",
    "ASC",
    "ASCII",
    "ASENSITIVE",
    "ASSERTION",
    "ASYMMETRIC",
    "AT",
    "ATOMIC",
    "ATTACH",
    "ATTRIBUTE",
    "AUTH",
    "AUTHORIZATION",
    "AUTHORIZE",
    "AUTO",
    "AVG",
    "BACK",
    "BACKUP",
    "BASE",
    "BATCH",
    "BEFORE",
    "BEGIN",
    "BETWEEN",
    "BIGINT",
    "BINARY",
    "BIT",
    "BLOB",
    "BLOCK",
    "BOOLEAN",
    "BOTH",
    "BREADTH",
    "BUCKET",
    "BULK",
    "BY",
    "BYTE",
    "CALL",
    "CALLED",
    "CALLING",
    "CAPACITY",
    "CASCADE",
    "CASCADED",
    "CASE",
    "CAST",
    "CATALOG",
    "CHAR",
    "CHARACTER",
    "CHECK",
    "CLASS",
    "CLOB",
    "CLOSE",
    "CLUSTER",
    "CLUSTERED",
    "CLUSTERING",
    "CLUSTERS",
    "COALESCE",
    "COLLATE",
    "COLLATION",
    "COLLECTION",
    "COLUMN",
    "COLUMNS",
    "COMBINE",
    "COMMENT",
    "COMMIT",
    "COMPACT",
    "COMPILE",
    "COMPRESS",
    "CONDITION",
    "CONFLICT",
    "CONNECT",
    "CONNECTION",
    "CONSISTENCY",
    "CONSISTENT",
    "CONSTRAINT",
    "CONSTRAINTS",
    "CONSTRUCTOR",
    "CONSUMED",
    "CONTINUE",
    "CONVERT",
    "COPY",
    "CORRESPONDING",
    "COUNT",
    "COUNTER",
    "CREATE",
    "CROSS",
    "CUBE",
    "CURRENT",
    "CURSOR",
    "CYCLE",
    "DATA",
    "DATABASE",
    "DATE",
    "DATETIME",
    "DAY",
    "DEALLOCATE",
    "DEC",
    "DECIMAL",
    "DECLARE",
    "DEFAULT",
    "DEFERRABLE",
    "DEFERRED",
    "DEFINE",
    "DEFINED",
    "DEFINITION",
    "DELETE",
    "DELIMITED",
    "DEPTH",
    "DEREF",
    "DESC",
    "DESCRIBE",
    "DESCRIPTOR",
    "DETACH",
    "DETERMINISTIC",
    "DIAGNOSTICS",
    "DIRECTORIES",
    "DISABLE",
    "DISCONNECT",
    "DISTINCT",
    "DISTRIBUTE",
    "DO",
    "DOMAIN",
    "DOUBLE",
    "DROP",
    "DUMP",
    "DURATION",
    "DYNAMIC",
    "EACH",
    "ELEMENT",
    "ELSE",
    "ELSEIF",
    "EMPTY",
    "ENABLE",
    "END",
    "EQUAL",
    "EQUALS",
    "ERROR",
    "ESCAPE",
    "ESCAPED",
    "EVAL",
    "EVALUATE",
    "EXCEEDED",
    "EXCEPT",
    "EXCEPTION",
    "EXCEPTIONS",
    "EXCLUSIVE",
    "EXEC",
    "EXECUTE",
    "EXISTS",
    "EXIT",
    "EXPLAIN",
    "EXPLODE",
    "EXPORT",
    "EXPRESSION",
    "EXTENDED",
    "EXTERNAL",
    "EXTRACT",
    "FAIL",
    "FALSE",
    "FAMILY",
    "FETCH",
    "FIELDS",
    "FILE",
    "FILTER",
    "FILTERING",
    "FINAL",
    "FINISH",
    "FIRST",
    "FIXED",
    "FLATTERN",
    "FLOAT",
    "FOR",
    "FORCE",
    "FOREIGN",
    "FORMAT",
    "FORWARD",
    "FOUND",
    "FREE",
    "FROM",
    "FULL",
    "FUNCTION",
    "FUNCTIONS",
    "GENERAL",
    "GENERATE",
    "GET",
    "GLOB",
    "GLOBAL",
    "GO",
    "GOTO",
    "GRANT",
    "GREATER",
    "GROUP",
    "GROUPING",
    "HANDLER",
    "HASH",
    "HAVE",
    "HAVING",
    "HEAP",
    "HIDDEN",
    "HOLD",
    "HOUR",
    "IDENTIFIED",
    "IDENTITY",
    "IF",
    "IGNORE",
    "IMMEDIATE",
    "IMPORT",
    "IN",
    "INCLUDING",
    "INCLUSIVE",
    "INCREMENT",
    "INCREMENTAL",
    "INDEX",
    "INDEXED",
    "INDEXES",
    "INDICATOR",
    "INFINITE",
    "INITIALLY",
    "INLINE",
    "INNER",
    "INNTER",
    "INOUT",
    "INPUT",
    "INSENSITIVE",
    "INSERT",
    "INSTEAD",
    "INT",
    "INTEGER",
    "INTERSECT",
    "INTERVAL",
    "INTO",
    "INVALIDATE",
    "IS",
    "ISOLATION",
    "ITEM",
    "ITEMS",
    "ITERATE",
    "JOIN",
    "KEY",
    "KEYS",
    "LAG",
    "LANGUAGE",
    "LARGE",
    "LAST",
    "LATERAL",
    "LEAD",
    "LEADING",
    "LEAVE",
    "LEFT",
    "LENGTH",
    "LESS",
    "LEVEL",
    "LIKE",
    "LIMIT",
    "LIMITED",
    "LINES",
    "LIST",
    "LOAD",
    "LOCAL",
    "LOCALTIME",
    "LOCALTIMESTAMP",
    "LOCATION",
    "LOCATOR",
    "LOCK",
    "LOCKS",
    "LOG",
    "LOGED",
    "LONG",
    "LOOP",
    "LOWER",
    "MAP",
    "MATCH",
    "MATERIALIZED",
    "MAX",
    "MAXLEN",
    "MEMBER",
    "MERGE",
    "METHOD",
    "METRICS",
    "MIN",
    "MINUS",
    "MINUTE",
    "MISSING",
    "MOD",
    "MODE",
    "MODIFIES",
    "MODIFY",
    "MODULE",
    "MONTH",
    "MULTI",
    "MULTISET",
    "NAME",
    "NAMES",
    "NATIONAL",
    "NATURAL",
    "NCHAR",
    "NCLOB",
    "NEW",
    "NEXT",
    "NO",
    "NONE",
    "NOT",
    "NULL",
    "NULLIF",
    "NUMBER",
    "NUMERIC",
    "OBJECT",
    "OF",
    "OFFLINE",
    "OFFSET",
    "OLD",
    "ON",
    "ONLINE",
    "ONLY",
    "OPAQUE",
    "OPEN",
    "OPERATOR",
    "OPTION",
    "OR",
    "ORDER",
    "ORDINALITY",
    "OTHER",
    "OTHERS",
    "OUT",
    "OUTER",
    "OUTPUT",
    "OVER",
    "OVERLAPS",
    "OVERRIDE",
    "OWNER",
    "PAD",
    "PARALLEL",
    "PARAMETER",
    "PARAMETERS",
    "PARTIAL",
    "PARTITION",
    "PARTITIONED",
    "PARTITIONS",
    "PATH",
    "PERCENT",
    "PERCENTILE",
    "PERMISSION",
    "PERMISSIONS",
    "PIPE",
    "PIPELINED",
    "PLAN",
    "POOL",
    "POSITION",
    "PRECISION",
    "PREPARE",
    "PRESERVE",
    "PRIMARY",
    "PRIOR",
    "PRIVATE",
    "PRIVILEGES",
    "PROCEDURE",
    "PROCESSED",
    "PROJECT",
    "PROJECTION",
    "PROPERTY",
    "PROVISIONING",
    "PUBLIC",
    "PUT",
    "QUERY",
    "QUIT",
    "QUORUM",
    "RAISE",
    "RANDOM",
    "RANGE",
    "RANK",
    "RAW",
    "READ",
    "READS",
    "REAL",
    "REBUILD",
    "RECORD",
    "RECURSIVE",
    "REDUCE",
    "REF",
    "REFERENCE",
    "REFERENCES",
    "REFERENCING",
    "REGEXP",
    "REGION",
    "REINDEX",
    "RELATIVE",
    "RELEASE",
    "REMAINDER",
    "RENAME",
    "REPEAT",
    "REPLACE",
    "REQUEST",
    "RESET",
    "RESIGNAL",
    "RESOURCE",
    "RESPONSE",
    "RESTORE",
    "RESTRICT",
    "RESULT",
    "RETURN",
    "RETURNING",
    "RETURNS",
    "REVERSE",
    "REVOKE",
    "RIGHT",
    "ROLE",
    "ROLES",
    "ROLLBACK",
    "ROLLUP",
    "ROUTINE",
    "ROW",
    "ROWS",
    "RULE",
    "RULES",
    "SAMPLE",
    "SATISFIES",
    "SAVE",
    "SAVEPOINT",
    "SCAN",
    "SCHEMA",
    "SCOPE",
    "SCROLL",
    "SEARCH",
    "SECOND",
    "SECTION",
    "SEGMENT",
    "SEGMENTS",
    "SELECT",
    "SELF",
    "SEMI",
    "SENSITIVE",
    "SEPARATE",
    "SEQUENCE",
    "SERIALIZABLE",
    "SESSION",
    "SET",
    "SETS",
    "SHARD",
    "SHARE",
    "SHARED",
    "SHORT",
    "SHOW",
    "SIGNAL",
    "SIMILAR",
    "SIZE",
    "SKEWED",
    "SMALLINT",
    "SNAPSHOT",
    "SOME",
    "SOURCE",
    "SPACE",
    "SPACES",
    "SPARSE",
    "SPECIFIC",
    "SPECIFICTYPE",
    "SPLIT",
    "SQL",
    "SQLCODE",
    "SQLERROR",
    "SQLEXCEPTION",
    "SQLSTATE",
    "SQLWARNING",
    "START",
    "STATE",
    "STATIC",
    "STATUS",
    "STORAGE",
    "STORE",
    "STORED",
    "STREAM",
    "STRING",
    "STRUCT",
    "STYLE",
    "SUB",
    "SUBMULTISET",
    "SUBPARTITION",
    "SUBSTRING",
    "SUBTYPE",
    "SUM",
    "SUPER",
    "SYMMETRIC",
    "SYNONYM",
    "SYSTEM",
    "TABLE",
    "TABLESAMPLE",
    "TEMP",
    "TEMPORARY",
    "TERMINATED",
    "TEXT",
    "THAN",
    "THEN",
    "THROUGHPUT",
    "TIME",
    "TIMESTAMP",
    "TIMEZONE",
    "TINYINT",
    "TO",
    "TOKEN",
    "TOTAL",
    "TOUCH",
    "TRAILING",
    "TRANSACTION",
    "TRANSFORM",
    "TRANSLATE",
    "TRANSLATION",
    "TREAT",
    "TRIGGER",
    "TRIM",
    "TRUE",
    "TRUNCATE",
    "TTL",
    "TUPLE",
    "TYPE",
    "UNDER",
    "UNDO",
    "UNION",
    "UNIQUE",
    "UNIT",
    "UNKNOWN",
    "UNLOGGED",
    "UNNEST",
    "UNPROCESSED",
    "UNSIGNED",
    "UNTIL",
    "UPDATE",
    "UPPER",
    "URL",
    "USAGE",
    "USE",
    "USER",
    "USERS",
    "USING",
    "UUID",
    "VACUUM",
    "VALUE",
    "VALUED",
    "VALUES",
    "VARCHAR",
    "VARIABLE",
    "VARIANCE",
    "VARINT",
    "VARYING",
    "VIEW",
    "VIEWS",
    "VIRTUAL",
    "VOID",
    "WAIT",
    "WHEN",
    "WHENEVER",
    "WHERE",
    "WHILE",
    "WINDOW",
    "WITH",
    "WITHIN",
    "WITHOUT",
    "WORK",
    "WRAPPED",
    "WRITE",
    "YEAR",
    "ZONE",
]
