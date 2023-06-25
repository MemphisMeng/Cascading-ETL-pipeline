from diagrams import Diagram
from diagrams.aws.database import Dynamodb
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.integration import SimpleQueueServiceSqsQueue
from diagrams.custom import Custom

with Diagram("Cascading ETL Pipeline", show=False):
    api = Custom('API', './api.png')
    branch_function = LambdaFunction('Branch Collector')
    employee_queue = SimpleQueueServiceSqsQueue('Employee Queue')
    branch_table = Dynamodb('Branch Table')
    salesperson_function = LambdaFunction('Salesperson Collector')
    sale_queue = SimpleQueueServiceSqsQueue('Sale Queue')
    salesperson_table = Dynamodb('Salesperson Table')
    sale_function = LambdaFunction('Sale Collector')
    sale_table = Dynamodb('Sale Table')

    api >> branch_function
    branch_function >> employee_queue
    branch_function >> branch_table
    employee_queue >> salesperson_function
    salesperson_function >> sale_queue
    salesperson_function >> salesperson_table
    sale_queue >> sale_function
    sale_function >>sale_table