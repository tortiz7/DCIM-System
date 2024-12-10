import os
import asyncio
from fastapi import FastAPI, Body
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from tools import (PrometheusQueryTool, AWSResourceTool, JenkinsTool, SlackNotificationTool, OPENAI_API_KEY)

# Initialize tools
prometheus_tool = PrometheusQueryTool(prometheus_url="http://prometheus:9090")
aws_tool = AWSResourceTool(region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
jenkins_tool = JenkinsTool(
    jenkins_url=os.getenv("JENKINS_URL", "http://jenkins:8080"),
    username=os.getenv("JENKINS_USER", "user"),
    token=os.getenv("JENKINS_TOKEN", "token")
)
slack_tool = SlackNotificationTool(
    slack_token=os.getenv("SLACK_BOT_TOKEN", ""),
    default_channel="#alerts"
)

tools = [prometheus_tool, aws_tool, jenkins_tool, slack_tool]

# Use OpenAI or another LLM. If using Ollama, replace with a custom LLM class.
llm = ChatOpenAI(
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

app = FastAPI()
scheduler = AsyncIOScheduler()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run_query")
async def run_query(query: str = Body(...)):
    """
    Run an ad-hoc query against the agent.
    Example: {"query": "Use prometheus_query tool with query 'node_load1' and summarize the results."}
    """
    response = agent.run(query)
    return {"response": response}

# Example periodic task every 5 minutes
@scheduler.scheduled_job("interval", minutes=5)
def periodic_task():
    query = "Use prometheus_query tool with query 'rate(node_cpu_seconds_total[5m])' and summarize the results."
    response = agent.run(query)
    print("Periodic task response:", response)

def start_scheduler():
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=8000)