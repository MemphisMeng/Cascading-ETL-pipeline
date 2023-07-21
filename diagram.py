from diagrams import Diagram, Edge, Cluster
from diagrams.aws.database import Dynamodb
from diagrams.aws.compute import LambdaFunction
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SimpleQueueServiceSqsQueue
from diagrams.custom import Custom

with Diagram("Cascading ETL Pipeline", show=False):
    api1 = Custom("API", "./api.png")
    api2 = Custom("API", "./api.png")
    api3 = Custom("API", "./api.png")

    branch_function = LambdaFunction("Branch Collector")
    employee_queue = SimpleQueueServiceSqsQueue("Salesperson Queue")
    branch_table = Dynamodb("Branch Table")
    salesperson_function = LambdaFunction("Salesperson Collector")
    sale_queue = SimpleQueueServiceSqsQueue("Sale Queue")
    salesperson_table = Dynamodb("Salesperson Table")
    sale_function = LambdaFunction("Sale Collector")
    sale_table = Dynamodb("Sale Table")

    with Cluster("Ingestion Pipeline"):
        api1 >> Edge(style='dashed') >> branch_function
        branch_function >> employee_queue
        branch_function >> branch_table

        api2 >> Edge(style='dashed') >> salesperson_function
        employee_queue >> salesperson_function
        salesperson_function >> sale_queue
        salesperson_function >> salesperson_table

        api3 >> Edge(style='dashed') >> sale_function
        sale_queue >> sale_function
        sale_function >> sale_table

    Cloudwatch('Monitor') - Edge(label="listen to") - branch_function
    Cloudwatch('Monitor') - Edge(label="listen to") - salesperson_function
    Cloudwatch('Monitor') - Edge(label="listen to") - sale_function