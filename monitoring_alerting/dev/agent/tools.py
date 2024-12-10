import os
import json
import requests
import boto3
import jenkins
from slack_sdk import WebClient
from langchain.tools import BaseTool

def get_secret(key: str, default: str = None) -> str:
    """
    Utility to read from either environment variable or a FILE variant if present.
    """
    file_var = os.getenv(f"{key}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, 'r') as f:
            return f.read().strip()
    return os.getenv(key, default)

# Secrets and keys
#SLACK_BOT_TOKEN = get_secret("SLACK_BOT_TOKEN", "")
# JENKINS_URL = get_secret("JENKINS_URL", "http://jenkins:8080")
# JENKINS_USER = get_secret("JENKINS_USER", "user")
# JENKINS_TOKEN = get_secret("JENKINS_TOKEN", "token")
AWS_ACCESS_KEY_ID = get_secret("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_secret("AWS_SECRET_ACCESS_KEY")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")

# Prometheus Query Tool
class PrometheusQueryTool(BaseTool):
    name = "prometheus_query"
    description = "Query Prometheus metrics using PromQL."

    def __init__(self, prometheus_url: str):
        super().__init__()
        self.prometheus_url = prometheus_url

    def _run(self, query: str) -> str:
        url = f"{self.prometheus_url}/api/v1/query"
        response = requests.get(url, params={"query": query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, indent=2)
        else:
            return f"Error querying Prometheus: {response.text}"

# AWS Resource Tool
class AWSResourceTool(BaseTool):
    name = "aws_resource_manager"
    description = "Interact with AWS (EC2, CloudWatch, ASG) via boto3."

    def __init__(self, region_name: str = "us-east-1"):
        super().__init__()
        self.session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=region_name
        )
        self.ec2 = self.session.client("ec2")
        # self.cloudwatch = self.session.client("cloudwatch")
        self.asg = self.session.client("autoscaling")

    def _run(self, command: str) -> str:
        """
        command: JSON string with structure:
        { "action": "describe_instances" | "scale_asg" | "get_metric_statistics", "params": {...} }
        """
        try:
            cmd = json.loads(command)
            action = cmd.get("action")
            params = cmd.get("params", {})

            if action == "describe_instances":
                response = self.ec2.describe_instances(**params)
                return json.dumps(response, indent=2)
            elif action == "scale_asg":
                response = self.asg.update_auto_scaling_group(**params)
                return "ASG updated successfully."
            # elif action == "get_metric_statistics":
            #     response = self.cloudwatch.get_metric_statistics(**params)
            #     return json.dumps(response, indent=2)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error executing AWS command: {str(e)}"

# Jenkins Tool
class JenkinsTool(BaseTool):
    name = "jenkins_api"
    description = "Query Jenkins for job/build status and logs."

    def __init__(self, jenkins_url: str, username: str, token: str):
        super().__init__()
        self.jenkins_server = jenkins.Jenkins(jenkins_url, username=username, password=token)

    def _run(self, command: str) -> str:
        """
        command: JSON string:
        { "action": "get_build_info" | "get_job_info", "params": {"job_name": "my-job", "build_number": 42} }
        """
        try:
            cmd = json.loads(command)
            action = cmd.get("action")
            params = cmd.get("params", {})
            if action == "get_job_info":
                job_name = params["job_name"]
                info = self.jenkins_server.get_job_info(job_name)
                return json.dumps(info, indent=2)
            elif action == "get_build_info":
                job_name = params["job_name"]
                build_number = params["build_number"]
                info = self.jenkins_server.get_build_info(job_name, build_number)
                return json.dumps(info, indent=2)
            else:
                return f"Unknown Jenkins action: {action}"
        except Exception as e:
            return f"Error interacting with Jenkins: {str(e)}"

# # Slack Notification Tool
# class SlackNotificationTool(BaseTool):
#     name = "slack_notifier"
#     description = "Send notifications to a Slack channel."

#     def __init__(self, slack_token: str, default_channel: str = "#alerts"):
#         super().__init__()
#         self.client = WebClient(token=slack_token)
#         self.default_channel = default_channel

#     def _run(self, message: str) -> str:
#         """
#         message: JSON string: { "channel": "#alerts", "text": "Alert message" }
#         """
#         try:
#             msg = json.loads(message)
#             channel = msg.get("channel", self.default_channel)
#             text = msg.get("text", "")
#             response = self.client.chat_postMessage(channel=channel, text=text)
#             return f"Message sent. Slack response: {response.data}"
#         except Exception as e:
#             return f"Error sending Slack message: {str(e)}"