import os
import json
import requests
import boto3
from langchain.tools import BaseTool
from typing import Optional, Dict
from pydantic import BaseModel, Field

class PrometheusQueryTool(BaseTool):
    """Tool for querying Prometheus metrics."""
    name = "prometheus_query"
    description = "Query Prometheus metrics using PromQL."
    prometheus_url: str = Field(..., description="Prometheus server URL")

    def _run(self, query: str) -> str:
        """Run a PromQL query against the Prometheus API."""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            response = requests.get(url, params={"query": query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return json.dumps(data, indent=2)
            else:
                return f"Error querying Prometheus: {response.text}"
        except Exception as e:
            return f"Error executing Prometheus query: {str(e)}"

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("_arun method is not implemented.")

class AWSResourceTool(BaseTool):
    """Tool for interacting with AWS resources."""
    name = "aws_resource_manager"
    description = "Interact with AWS (EC2, CloudWatch, ASG) via boto3."
    
    # Define fields for AWS configuration
    aws_access_key_id: str = Field(..., description="AWS access key ID")
    aws_secret_access_key: str = Field(..., description="AWS secret access key")
    region_name: str = Field(default="us-east-1", description="AWS region name")
    
    # Private attributes will be initialized in post_init
    _session: Optional[boto3.Session] = None
    _ec2_client: Optional[object] = None
    _asg_client: Optional[object] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.initialize_clients()

    def initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self._session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            self._ec2_client = self._session.client('ec2')
            self._asg_client = self._session.client('autoscaling')
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AWS clients: {str(e)}")

    @property
    def session(self):
        return self._session

    @property
    def ec2(self):
        return self._ec2_client

    @property
    def asg(self):
        return self._asg_client

    def _run(self, command: str) -> str:
        """Execute AWS actions based on the provided command."""
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
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error executing AWS command: {str(e)}"

    async def _arun(self, command: str) -> str:
        raise NotImplementedError("_arun method is not implemented.")