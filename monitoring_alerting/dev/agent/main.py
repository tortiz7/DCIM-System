import os
import asyncio
from fastapi import FastAPI, Body
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from tools import AWSResourceTool, PrometheusQueryTool
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_secret(name: str, default: str = None) -> str:
    """
    Read a Docker secret from the /run/secrets directory.
    If the secret is not found, return the provided default value.
    """
    path = f"/run/secrets/{name.lower()}"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return os.getenv(name, default)

# Read and validate required secrets
required_secrets = {
    "OPENAI_API_KEY": "openai_api_key",
    "AWS_ACCESS_KEY_ID": "aws_access_key_id",
    "AWS_SECRET_ACCESS_KEY": "aws_secret_access_key",
}

secrets = {}
for env_var, secret_name in required_secrets.items():
    value = read_secret(secret_name)
    if not value:
        raise ValueError(f"{env_var} is not set")
    secrets[env_var] = value

# Initialize tools
try:
    # Initialize Prometheus tool
    prometheus_tool = PrometheusQueryTool(
        prometheus_url=os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    )
    
    # Initialize AWS tool
    aws_tool = AWSResourceTool(
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=secrets["AWS_SECRET_ACCESS_KEY"]
    )

    # Combine available tools
    tools = [prometheus_tool, aws_tool]

    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=secrets["OPENAI_API_KEY"]
    )

    # Initialize the agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
except Exception as e:
    logger.error(f"Error initializing tools or agent: {e}")
    raise

# Create FastAPI application
app = FastAPI()

# Initialize scheduler
scheduler = AsyncIOScheduler()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/run_query")
async def run_query(query: str = Body(...)):
    """
    Run an ad-hoc query against the agent.
    Example: {"query": "Use prometheus_query tool with query 'node_load1' and summarize the results."}
    """
    try:
        response = agent.run(query)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error running query: {e}")
        return {"error": str(e)}

@scheduler.scheduled_job("interval", minutes=5)
async def periodic_task():
    """Scheduled task to run a query every 5 minutes"""
    query = "Use prometheus_query tool with query 'rate(node_cpu_seconds_total[5m])' and summarize the results."
    try:
        response = await agent.arun(query)
        logger.info(f"Periodic task response: {response}")
    except Exception as e:
        logger.error(f"Error during periodic task: {e}")

@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the application starts"""
    scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)