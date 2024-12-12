import os
import json
import logging
from shared.tools import AWSResourceTool

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("REGION_NAME", "us-east-1")
    bucket_name = "your-s3-bucket-name"
    output_file = "findings_report.json"

    aws_tool = AWSResourceTool(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )

    logging.info("Starting reporting agent...")

    try:
        # Load analytics report
        with open("/app/logs/analytics_report.json", "r") as f:
            analytics_report = json.load(f)

        # Load monitoring report
        with open("/app/monitoring_report.json", "r") as f:
            monitoring_report = json.load(f)

        # Combine reports
        findings = {
            "analytics": analytics_report,
            "monitoring": monitoring_report
        }
        logging.info("Combined Findings: %s", json.dumps(findings, indent=2))

        # Save findings to file
        findings_path = f"/app/{output_file}"
        with open(findings_path, "w") as f:
            json.dump(findings, f, indent=2)
        logging.info("Findings saved locally to %s", findings_path)

        # Upload findings to S3
        upload_command = json.dumps({
            "action": "upload_to_s3",
            "params": {
                "bucket_name": bucket_name,
                "file_name": output_file,
                "content": json.dumps(findings)
            }
        })
        aws_tool._run(upload_command)
        logging.info("Findings uploaded to S3: %s/%s", bucket_name, output_file)
    except Exception as e:
        logging.error("Error in reporting: %s", str(e))

if __name__ == "__main__":
    main()