import os
import time
import requests
import pandas as pd
from prophet import Prophet

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://pushgateway:9091')

end_time = int(time.time())
start_time = end_time - 43200
step = '300s'

query = 'node_load1'

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
    result = data['data']['result'][0]
    values = result['values']
    df = pd.DataFrame(values, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'], unit='s')
    df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(method='ffill').fillna(0)

    m = Prophet(daily_seasonality=False)
    m.fit(df)
    future = m.make_future_dataframe(periods=12, freq='5min')
    forecast = m.predict(future)
    predicted_usage = forecast.iloc[-1]['yhat']

push_data = f"predicted_usage {predicted_usage}\n"
requests.post(f"{PUSHGATEWAY_URL}/metrics/job/ml_forecast", data=push_data)