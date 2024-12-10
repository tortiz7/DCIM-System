FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Run the FastAPI app which also starts the scheduler
CMD ["python", "main.py"]