import os
import time
import requests
import pandas as pd
from prophet import Prophet

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')

# Query last 12h of CPU usage
end_time = int(time.time())
start_time = end_time - 43200
step = '300s'  # 5min steps

query = 'avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)'

r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
    'query': query,
    'start': start_time,
    'end': end_time,
    'step': step
})

data = r.json()

if data['status'] != 'success' or len(data['data']['result']) == 0:
    predicted_usage = 0.5
else:
    result = data['data']['result'][0]  # assume one instance for simplicity
    values = result['values']
    df = pd.DataFrame(values, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'], unit='s')
    df['y'] = df['y'].astype(float)
    
    # Prophet forecasting
    m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
    m.fit(df)
    future = m.make_future_dataframe(periods=12, freq='5min')  # predict next hour
    forecast = m.predict(future)
    # Take the last predicted value as the next-hour CPU usage estimate
    predicted_usage = forecast.iloc[-1]['yhat']

# Push to Pushgateway
push_data = f"predicted_cpu_usage {predicted_usage}\n"
requests.post(f"{PUSHGATEWAY_URL}/metrics/job/ml_forecast", data=push_data)