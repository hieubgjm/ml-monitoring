FROM apache/airflow:2.10.2

# The official image does not include Airflow's optional StatsD client extra.
# StatsD Exporter turns the emitted metrics into Prometheus metrics.
RUN pip install --no-cache-dir statsd==4.0.1
