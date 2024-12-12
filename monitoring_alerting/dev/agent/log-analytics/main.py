import os
import json
import logging
from shared.tools import LogAnalyticsTool

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    log_directory = "/app/logs"
    analytics_tool = LogAnalyticsTool(log_directory=log_directory)

    logging.info("Starting log analytics...")
    try:
        command = "Analyze logs to generate analytics report"
        analytics_result = analytics_tool._run(command)
        logging.info("Log Analytics Result: %s", analytics_result)

        # Save analytics report to a file
        report_path = os.path.join(log_directory, "analytics_report.json")
        with open(report_path, "w") as f:
            json.dump(json.loads(analytics_result), f, indent=2)
        logging.info("Analytics report saved to %s", report_path)
    except Exception as e:
        logging.error("Error in log analytics: %s", str(e))

if __name__ == "__main__":
    main()