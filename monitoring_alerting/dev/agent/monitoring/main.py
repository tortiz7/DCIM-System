import os
import json
import logging
from shared.tools import PrometheusQueryTool

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    prometheus_tool = PrometheusQueryTool(prometheus_url=prometheus_url)

    logging.info("Starting Prometheus monitoring...")
    try:
        query = 'anomaly_score{metric="container_cpu_usage_seconds_total"} > 0.8'
        monitoring_result = prometheus_tool._run(query)
        logging.info("Prometheus Query Result: %s", monitoring_result)

        # Save monitoring result to a file
        report_path = "/app/monitoring_report.json"
        with open(report_path, "w") as f:
            json.dump(json.loads(monitoring_result), f, indent=2)
        logging.info("Monitoring report saved to %s", report_path)
    except Exception as e:
        logging.error("Error in monitoring: %s", str(e))

if __name__ == "__main__":
    main()