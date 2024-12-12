FROM python:3.9-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

WORKDIR /agent

# Copy requirements first to leverage Docker cache
COPY shared/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install prometheus_client requests boto3

# Copy shared code and tools
COPY shared/ ./shared/
COPY agent/analytics/main.py ./main.py
COPY scripts/analyze_findings.sh ./scripts/analyze_findings.sh

# Allow build-time arguments to specify which agent to build
ARG AGENT_NAME

# Copy the specific agent's code
COPY agent/${AGENT_NAME}/main.py ./main.py

# Set the default command to run the agent
CMD ["python", "./main.py"]