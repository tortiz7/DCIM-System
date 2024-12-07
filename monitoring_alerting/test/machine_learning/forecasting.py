# forecasting.py
import os
import time
import logging
import requests
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prophet import Prophet

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Environment Variables
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://pushgateway:9091')

# Forecasting Parameters
LOOKBACK_SECONDS = int(os.getenv('FORECAST_LOOKBACK', '86400'))  # 24 hours
STEP = os.getenv('FORECAST_STEP', '60s')  # 1 minute
HORIZON = int(os.getenv('FORECAST_HORIZON', '60'))  # Forecast horizon in minutes
MIN_FORECAST_ROWS = int(os.getenv('MIN_FORECAST_ROWS', '2'))  # Minimum rows required for forecasting

# List of Metrics for Forecasting
FORECAST_METRICS = [
    # CPU Metrics
    'node_cpu_seconds_total',
    'node_schedstat_running_seconds_total',

    # Memory Metrics
    'node_memory_MemTotal_bytes',
    'node_memory_MemAvailable_bytes',
    'node_memory_Cached_bytes',
    'node_memory_Buffers_bytes',

    # Disk I/O Metrics
    'node_disk_read_bytes_total',
    'node_disk_written_bytes_total',
    'node_disk_io_time_seconds_total',

    # Network Metrics
    'node_network_receive_bytes_total',
    'node_network_transmit_bytes_total',

    # System Load Metrics
    'node_load1',
    'node_load5',
    'node_load15',

    # Process and Application Metrics
    'process_cpu_seconds_total',
    'process_resident_memory_bytes',
    'go_gc_duration_seconds',
    'go_goroutines',

    # Additional Useful Metrics
    'node_nf_conntrack_entries'
]

def fetch_prometheus_data(query, start_time, end_time, step):
    """
    Fetch time series data from Prometheus for a given query.
    """
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
            'query': query,
            'start': start_time,
            'end': end_time,
            'step': step
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] != 'success':
            logging.error(f"Prometheus query failed for {query}: {data}")
            return []
        return data['data']['result']
    except Exception as e:
        logging.exception(f"Error fetching data from Prometheus for {query}")
        return []

def forecast_timeseries(df, horizon_minutes=60, min_rows=2):
    """
    Use Prophet to forecast the next 'horizon_minutes' minutes.
    """
    if df.empty or df.shape[0] < min_rows:
        logging.warning(f"Dataframe has {df.shape[0]} rows, which is less than the required {min_rows}. Returning neutral prediction.")
        return 0.5
    try:
        logging.debug(f"Dataframe size: {df.shape[0]} rows")
        m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon_minutes // 5, freq='5min')  # Assuming step is 5 minutes
        forecast = m.predict(future)
        predicted_value = forecast.iloc[-1]['yhat']
        logging.debug(f"Forecasted value: {predicted_value}")
        return predicted_value
    except Exception as e:
        logging.exception("Error during forecasting with Prophet")
        return 0.5  # Return a neutral prediction in case of failure

def process_labels(labels, default_metric='unknown_metric'):
    """
    Process labels by removing '__name__' and adding 'metric' label.
    If no labels remain, add a default 'metric' label.
    """
    # Remove '__name__'
    labels = {k: v for k, v in labels.items() if k != '__name__'}

    # Add 'metric' label if '__name__' was present
    if '__name__' in labels:
        labels['metric'] = labels.pop('__name__')

    # If no labels remain, add a default 'metric' label
    if not labels:
        labels = {'metric': default_metric}

    return labels

def push_forecast(predicted_usage, labels):
    """
    Push the forecasted usage to the Pushgateway with appropriate labels.
    """
    try:
        labels = process_labels(labels, default_metric='node_load1')  # Replace with appropriate default if needed

        registry = CollectorRegistry()
        g = Gauge('predicted_usage', 'Forecasted usage by ML model', labelnames=labels.keys(), registry=registry)
        g.labels(**labels).set(predicted_usage)
        push_to_gateway(PUSHGATEWAY_URL, job='ml_forecast', registry=registry)
        logging.info(f"Pushed predicted usage {predicted_usage} with labels {labels}")
    except Exception as e:
        logging.exception("Error pushing forecast to Pushgateway")

def main():
    """
    Main function to iterate over all forecasting metrics, perform forecasting, and push results.
    """
    end_time = int(time.time())
    start_time = end_time - LOOKBACK_SECONDS

    for metric in FORECAST_METRICS:
        logging.info(f"Processing metric for forecasting: {metric}")
        results = fetch_prometheus_data(metric, start_time, end_time, STEP)

        if not results:
            push_forecast(0.5, {'metric': metric})
            continue

        for ts in results:
            values = ts['values']
            metric_labels = ts.get('metric', {})
            # Convert timestamp to datetime
            df = pd.DataFrame(values, columns=['ds', 'y'])
            df['ds'] = pd.to_datetime(df['ds'], unit='s')
            df['y'] = pd.to_numeric(df['y'], errors='coerce').ffill().fillna(0)  # Updated fillna usage

            predicted = forecast_timeseries(df, horizon_minutes=HORIZON, min_rows=MIN_FORECAST_ROWS)
            push_forecast(predicted, metric_labels)

if __name__ == "__main__":
    main()