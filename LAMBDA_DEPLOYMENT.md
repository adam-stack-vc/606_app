# AWS Lambda Deployment Guide for fetch_content_lambda.py

## Overview
This Lambda function fetches web content using ScrapingBee API and saves markdown files to S3.

## Prerequisites
- AWS Account with Lambda and S3 access
- ScrapingBee API Key
- Python 3.9+ runtime

## Setup Instructions

### 1. Create S3 Bucket
```bash
aws s3 mb s3://your-bucket-name
```

### 2. Create Lambda Function

#### Option A: Using AWS Console
1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `fetch-content-processor`
5. Runtime: Python 3.11
6. Architecture: x86_64
7. Click "Create function"

#### Option B: Using AWS CLI
```bash
aws lambda create-function \
  --function-name fetch-content-processor \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-s3-execution-role \
  --handler fetch_content_lambda.lambda_handler \
  --timeout 900 \
  --memory-size 512
```

### 3. Package and Deploy

#### Create deployment package:
```bash
# Create a temporary directory
mkdir lambda_package
cd lambda_package

# Install dependencies
pip install -r ../lambda_requirements.txt -t .

# Copy the Lambda function
cp ../fetch_content_lambda.py .

# Create ZIP file
zip -r ../fetch_content_lambda.zip .

# Clean up
cd ..
rm -rf lambda_package
```

#### Upload to Lambda:
```bash
aws lambda update-function-code \
  --function-name fetch-content-processor \
  --zip-file fileb://fetch_content_lambda.zip
```

### 4. Configure Environment Variables

Set the ScrapingBee API key:

```bash
aws lambda update-function-configuration \
  --function-name fetch-content-processor \
  --environment Variables={SCRAPINGBEE_API_KEY=YOUR_API_KEY_HERE}
```

Or via AWS Console:
1. Go to Lambda function
2. Configuration → Environment variables
3. Add key: `SCRAPINGBEE_API_KEY`
4. Add value: Your ScrapingBee API key

### 5. Configure IAM Permissions

The Lambda function needs an IAM role with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 6. Configure Function Settings

- **Timeout**: 15 minutes (900 seconds) - Content fetching can take time
- **Memory**: 512 MB - Should be sufficient for processing
- **Ephemeral storage**: 512 MB (default)

```bash
aws lambda update-function-configuration \
  --function-name fetch-content-processor \
  --timeout 900 \
  --memory-size 512
```

## Usage

### Invoke the Lambda Function

#### Test Event Example:
```json
{
  "input_bucket": "your-bucket-name",
  "input_key": "input/filtered_links.csv",
  "output_bucket": "your-bucket-name",
  "output_prefix": "output/markdown"
}
```

#### Via AWS CLI:
```bash
aws lambda invoke \
  --function-name fetch-content-processor \
  --payload file://test_event.json \
  response.json

cat response.json
```

#### Via AWS Console:
1. Go to Lambda function
2. Click "Test" tab
3. Create new test event with the JSON above
4. Click "Test"

### Input CSV Format

The input CSV should have these columns:
- `company_name`: Name of the company
- `url`: URL to fetch
- `title`: Title of the content
- `date`: Date of the content
- `category`: Category/classification

Example:
```csv
company_name,url,title,date,category
"Robinhood","https://example.com/article","Article Title","2024-01-01","PFOF"
```

### Output Structure

The function creates these files in S3:

1. **Markdown files**: `{output_prefix}/{safe_filename}.md`
   - Contains YAML frontmatter with metadata
   - Followed by markdown content

2. **Results JSON**: `{output_prefix}/fetch_results.json`
   - Detailed results for each fetched URL

3. **Summary CSV**: `{output_prefix}/fetch_summary.csv`
   - Summary of all fetch operations

## Response Format

### Success Response:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Content fetch completed successfully",
    "statistics": {
      "total_companies": 5,
      "total_pages": 25,
      "successful_fetches": 23,
      "failed_fetches": 2,
      "success_rate": 92.0
    },
    "results_key": "output/markdown/fetch_results.json",
    "summary_key": "output/markdown/fetch_summary.csv",
    "output_location": "s3://your-bucket-name/output/markdown/"
  }
}
```

### Error Response:
```json
{
  "statusCode": 500,
  "body": {
    "error": "Error message here",
    "message": "Error processing content fetch"
  }
}
```

## Monitoring

### CloudWatch Logs
View logs in CloudWatch:
```bash
aws logs tail /aws/lambda/fetch-content-processor --follow
```

### CloudWatch Metrics
Monitor:
- Invocations
- Duration
- Errors
- Throttles

## Cost Considerations

- **Lambda**: ~$0.20 per 1M requests + compute time
- **S3**: Storage costs for markdown files
- **ScrapingBee**: Based on your API plan
- **CloudWatch**: Log storage costs

## Troubleshooting

### Common Issues

1. **Timeout errors**: Increase timeout or process in batches
2. **Memory errors**: Increase memory allocation
3. **Permission errors**: Check IAM role permissions
4. **API errors**: Verify ScrapingBee API key and quota

### Debug Mode

Add more logging in the function:
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
```

## Scaling Considerations

For large batches:
1. Split input CSV into smaller chunks
2. Use Step Functions to orchestrate multiple Lambda invocations
3. Consider using Lambda concurrency controls
4. Implement retry logic for failed fetches

## Alternative: Use S3 Event Trigger

You can configure the Lambda to automatically trigger when a CSV is uploaded:

1. Add S3 trigger to Lambda
2. Configure for `s3:ObjectCreated:*` events
3. Filter for `.csv` suffix
4. Parse bucket/key from event automatically

Example event structure from S3:
```python
def lambda_handler(event, context):
    # Extract S3 info from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Use these instead of event parameters
    ...
```


