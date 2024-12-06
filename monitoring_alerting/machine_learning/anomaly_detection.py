import os
import time
import requests
import pandas as pd
from sklearn.ensemble import IsolationForest

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')

end_time = int(time.time())
start_time = end_time - 3600  # last 1 hour
step = '60s'

# Define queries for different containers and metrics:
# 1. Ralph container CPU usage (using 5m rate of cpu usage)
ralph_query = 'rate(container_cpu_usage_seconds_total{container_name="ralph"}[5m])'

# 2. Nginx container CPU usage
nginx_query = 'rate(container_cpu_usage_seconds_total{container_name="nginx"}[5m])'

# 3. Chatbot container memory usage (no rate needed since memory is a gauge)
chatbot_query = 'container_memory_working_set_bytes{container_name="chatbot"}'

queries = [
    ("ralph", ralph_query),
    ("nginx", nginx_query),
    ("chatbot", chatbot_query)
]

def fetch_data_and_detect_anomaly(query):
    r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
        'query': query,
        'start': start_time,
        'end': end_time,
        'step': step
    })
    data = r.json()

    if data['status'] != 'success' or len(data['data']['result']) == 0:
        # If no data returned for this metric, return a neutral anomaly score.
        return 0.5
    else:
        # Assume single time series for simplicity. If multiple, handle accordingly.
        result = data['data']['result'][0]
        values = result['values']  # [[timestamp, value], ...]
        df = pd.DataFrame(values, columns=['timestamp', 'value'])
        df['value'] = df['value'].astype(float).fillna(df['value'].mean())

        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(df[['value']])

        scores = model.decision_function(df[['value']])
        # Last data point anomaly score
        anomaly_score = 1 - (scores[-1] + 1) / 2
        return anomaly_score

# Process each query and push results to Pushgateway
for container_name, q in queries:
    anomaly_score = fetch_data_and_detect_anomaly(q)
    # Push anomaly score with a label to differentiate containers
    push_data = f'anomaly_score{{container="{container_name}"}} {anomaly_score}\n'
    requests.post(f"{PUSHGATEWAY_URL}/metrics/job/ml_anomaly", data=push_data)