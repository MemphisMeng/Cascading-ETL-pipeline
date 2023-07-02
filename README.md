# Cascading ETL pipeline
Tutorial of AWS-based ETL pipeline development

## ERD
![](./cascading_etl_pipeline.png)

## Running this repo
### Prerequisite: [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

- Environment setup
In each folder, run
```
pip install -r requirements.txt
```

- Build:
```
sam build
```
- Deploy:
```
sam deploy
```
- Local Invoke:
```
sam local invoke "BranchCollector" -e event.json --env-vars env.json
```