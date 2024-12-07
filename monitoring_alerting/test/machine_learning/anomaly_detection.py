import os
import time
import requests
import pandas as pd
from sklearn.ensemble import IsolationForest

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://pushgateway:9091')

end_time = int(time.time())
start_time = end_time - 3600
step = '60s'

# Using a simple metric: node_load1 from node_exporter
query = 'node_load1'

r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
    'query': query,
    'start': start_time,
    'end': end_time,
    'step': step
})
data = r.json()

if data['status'] != 'success' or len(data['data']['result']) == 0:
    anomaly_score = 0.5
else:
    result = data['data']['result'][0]
    values = result['values']
    df = pd.DataFrame(values, columns=['timestamp', 'value'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(method='ffill').fillna(0)

    model = IsolationForest(contamination=0.01, random_state=42)
    model.fit(df[['value']])
    scores = model.decision_function(df[['value']])
    anomaly_score = 1 - (scores[-1] + 1) / 2

push_data = f"anomaly_score {anomaly_score}\n"
requests.post(f"{PUSHGATEWAY_URL}/metrics/job/ml_anomaly", data=push_data)