# dev/shared/workflow_coordinator.py
from typing import Dict, Any
import os
import json
import logging
from datetime import datetime
from shared.tools import LogAnalyticsTool, PrometheusQueryTool, AWSResourceTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class WorkflowCoordinator:
    def __init__(self):
        self.reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
        self.log_directory = "/app/logs"
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        
        # Initialize tools
        self.log_tool = LogAnalyticsTool(log_directory=self.log_directory)
        self.prometheus_tool = PrometheusQueryTool(prometheus_url=self.prometheus_url)
        self.aws_tool = AWSResourceTool(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    def _coordinate_log_analysis(self) -> Dict[str, Any]:
        try:
            logging.info("Starting log analysis coordination")
            result = self.log_tool._run("Analyze logs to generate analytics report")
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "data": json.loads(result)
            }
        except Exception as e:
            logging.error(f"Log analysis failed: {str(e)}")
            raise

    def _coordinate_monitoring(self) -> Dict[str, Any]:
        try:
            logging.info("Starting monitoring coordination")
            queries = {
                "node_metrics": "node_memory_MemAvailable_bytes",
                "container_metrics": "container_memory_usage_bytes",
                "up_status": "up",
                "cadvisor_metrics": "container_cpu_usage_seconds_total",
                "anomaly_scores": 'anomaly_score{metric="container_cpu_usage_seconds_total"} > 0.8'
            }
            
            monitoring_results = {}
            for name, query in queries.items():
                result = self.prometheus_tool._run(query)
                monitoring_results[name] = json.loads(result)
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "data": monitoring_results
            }
        except Exception as e:
            logging.error(f"Monitoring failed: {str(e)}")
            raise

    def _coordinate_analytics(self, log_data: Dict, monitoring_data: Dict) -> Dict[str, Any]:
        try:
            logging.info("Starting analytics coordination")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            analysis_data = {
                "timestamp": timestamp,
                "log_analysis": log_data,
                "monitoring": monitoring_data
            }
            
            analysis_path = os.path.join(self.reports_dir, f"analysis_{timestamp}.json")
            os.makedirs(self.reports_dir, exist_ok=True)
            
            with open(analysis_path, "w") as f:
                json.dump(analysis_data, f, indent=2)
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "file_path": analysis_path,
                "data": analysis_data
            }
        except Exception as e:
            logging.error(f"Analytics failed: {str(e)}")
            raise

    def _coordinate_reporting(self, analysis_data: Dict) -> Dict[str, Any]:
        try:
            logging.info("Starting reporting coordination")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"report_{timestamp}.json"
            
            upload_command = json.dumps({
                "action": "upload_to_s3",
                "params": {
                    "bucket_name": os.getenv("S3_BUCKET_NAME"),
                    "file_name": f"reports/{report_file}",
                    "content": json.dumps(analysis_data)
                }
            })
            
            self.aws_tool._run(upload_command)
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "s3_path": f"reports/{report_file}"
            }
        except Exception as e:
            logging.error(f"Reporting failed: {str(e)}")
            raise

    def run_workflow(self) -> Dict[str, Any]:
        """Executes the complete workflow sequentially"""
        try:
            logging.info("Starting workflow execution")
            workflow_state = {
                "start_time": datetime.now().isoformat(),
                "status": "started"
            }
            
            # Execute steps sequentially
            log_result = self._coordinate_log_analysis()
            workflow_state["log_analysis"] = log_result
            
            monitoring_result = self._coordinate_monitoring()
            workflow_state["monitoring"] = monitoring_result
            
            analytics_result = self._coordinate_analytics(
                log_result.get("data", {}),
                monitoring_result.get("data", {})
            )
            workflow_state["analytics"] = analytics_result
            
            reporting_result = self._coordinate_reporting(analytics_result.get("data", {}))
            workflow_state["reporting"] = reporting_result
            
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = datetime.now().isoformat()
            
            logging.info("Workflow completed successfully")
            return workflow_state
            
        except Exception as e:
            logging.error(f"Workflow failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }