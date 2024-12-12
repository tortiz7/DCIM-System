# dev/shared/workflow_coordinator.py
from typing import Dict, Any
import os
import json
import logging
from datetime import datetime
from langgraph.graph import Graph, END
from shared.tools import LogAnalyticsTool, PrometheusQueryTool, AWSResourceTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/workflow.log')
    ]
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
        
        self.graph = self._build_graph()

    def _build_graph(self) -> Graph:
        workflow = Graph()

        # Define nodes
        workflow.add_node("log_analysis", self._coordinate_log_analysis)
        workflow.add_node("monitoring", self._coordinate_monitoring)
        workflow.add_node("analytics", self._coordinate_analytics)
        workflow.add_node("reporting", self._coordinate_reporting)
        workflow.add_node("error_handler", self._handle_error)

        # Define normal flow
        workflow.add_edge("log_analysis", "monitoring")
        workflow.add_edge("monitoring", "analytics")
        workflow.add_edge("analytics", "reporting")
        workflow.add_edge("reporting", END)

        # Define error handling paths
        workflow.add_edge("log_analysis", "error_handler", 
                         condition=lambda x: x.get("status") == "error")
        workflow.add_edge("monitoring", "error_handler", 
                         condition=lambda x: x.get("status") == "error")
        workflow.add_edge("analytics", "error_handler", 
                         condition=lambda x: x.get("status") == "error")
        workflow.add_edge("reporting", "error_handler", 
                         condition=lambda x: x.get("status") == "error")
        workflow.add_edge("error_handler", END)

        return workflow

    def _coordinate_log_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logging.info("Starting log analysis coordination")
            result = self.log_tool._run("Analyze logs to generate analytics report")
            result_data = json.loads(result)
            
            return {
                **state,
                "log_analysis": {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "data": result_data
                }
            }
        except Exception as e:
            logging.error(f"Log analysis failed: {str(e)}")
            return {
                **state,
                "status": "error",
                "component": "log_analysis",
                "error": str(e)
            }

    def _coordinate_monitoring(self, state: Dict[str, Any]) -> Dict[str, Any]:
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
                **state,
                "monitoring": {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "data": monitoring_results
                }
            }
        except Exception as e:
            logging.error(f"Monitoring failed: {str(e)}")
            return {
                **state,
                "status": "error",
                "component": "monitoring",
                "error": str(e)
            }

    def _coordinate_analytics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logging.info("Starting analytics coordination")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare analysis data
            analysis_data = {
                "timestamp": timestamp,
                "log_analysis": state.get("log_analysis", {}).get("data", {}),
                "monitoring": state.get("monitoring", {}).get("data", {})
            }
            
            # Save to file for analytics processing
            analysis_path = os.path.join(self.reports_dir, f"analysis_{timestamp}.json")
            os.makedirs(self.reports_dir, exist_ok=True)
            
            with open(analysis_path, "w") as f:
                json.dump(analysis_data, f, indent=2)
            
            logging.info(f"Analysis data saved to {analysis_path}")
            
            return {
                **state,
                "analytics": {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "file_path": analysis_path
                }
            }
        except Exception as e:
            logging.error(f"Analytics failed: {str(e)}")
            return {
                **state,
                "status": "error",
                "component": "analytics",
                "error": str(e)
            }

    def _coordinate_reporting(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logging.info("Starting reporting coordination")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"report_{timestamp}.json"
            
            # Prepare final report
            report_data = {
                "timestamp": timestamp,
                "log_analysis": state.get("log_analysis", {}),
                "monitoring": state.get("monitoring", {}),
                "analytics": state.get("analytics", {})
            }
            
            # Upload to S3
            upload_command = json.dumps({
                "action": "upload_to_s3",
                "params": {
                    "bucket_name": os.getenv("S3_BUCKET_NAME"),
                    "file_name": f"reports/{report_file}",
                    "content": json.dumps(report_data)
                }
            })
            
            self.aws_tool._run(upload_command)
            logging.info(f"Report uploaded to S3: reports/{report_file}")
            
            return {
                **state,
                "reporting": {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "s3_path": f"reports/{report_file}"
                }
            }
        except Exception as e:
            logging.error(f"Reporting failed: {str(e)}")
            return {
                **state,
                "status": "error",
                "component": "reporting",
                "error": str(e)
            }

    def _handle_error(self, state: Dict[str, Any]) -> Dict[str, Any]:
        error_component = state.get("component", "unknown")
        error_message = state.get("error", "Unknown error")
        logging.error(f"Error in {error_component}: {error_message}")
        
        # Implement retry logic if needed
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            logging.info(f"Attempting retry {retry_count + 1} for {error_component}")
            return {
                **state,
                "retry_count": retry_count + 1,
                "status": "retry"
            }
        
        return {
            **state,
            "status": "failed",
            "error_handled": True,
            "final_error": f"Component {error_component} failed after 3 retries: {error_message}"
        }

    def run_workflow(self) -> Dict[str, Any]:
        """Executes the complete workflow"""
        try:
            logging.info("Starting workflow execution")
            initial_state = {
                "start_time": datetime.now().isoformat(),
                "status": "started"
            }
            
            result = self.graph.run(initial_state)
            
            if result.get("status") == "failed":
                logging.error("Workflow failed", extra={"result": result})
            else:
                logging.info("Workflow completed successfully", extra={"result": result})
            
            return result
        except Exception as e:
            logging.error(f"Unexpected error in workflow execution: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }