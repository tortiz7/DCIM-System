# Base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /agent

# Copy shared dependencies and tools
COPY shared/ ./shared/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./shared/requirements.txt

# Copy the specific agent's main.py script
ARG AGENT_NAME
COPY agent/${AGENT_NAME}/main.py ./main.py

# Expose port (if applicable)
EXPOSE 7000

# Default command
CMD ["python", "./main.py"]