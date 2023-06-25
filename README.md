# Cascading-ETL-pipeline
Tutorial of AWS-based ETL pipeline development

## Running this repo
### Prerequisite: [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

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
echo '{"branches": ["Scranton"] }' | sam local invoke --event - "BranchCollector"
```