# 🎯 ML Model Monitoring System

**This project is for demonstration purposes.**
A production-ready machine learning monitoring system using MLFlow, Prometheus, Grafana and Evidently for real-time model observability and performance tracking.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Training Models](#-training-models)
- [Monitoring & Dashboards](#-monitoring--dashboards)
- [Evidently & Drift Monitoring](#-evidently--drift-monitoring)
- [Airflow & Alerting](#-airflow--alerting)
- [Simulations & Load Testing](#-simulations--load-testing)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

## CI Status

After you push to GitHub, the workflow at `.github/workflows/ci.yml` checks Docker Compose,
Prometheus and Alertmanager configurations, Python syntax, the alert receiver, and both custom
Docker images. A green check in the **Actions** tab means these checks passed.

---

## 🎯 Overview

This project demonstrates a complete MLOps pipeline with real-time monitoring for production machine learning models. It includes:

- **Model Training & Registry**: Train models and manage versions with MLFlow
- **Model Serving**: FastAPI-based REST API for model predictions
- **Metrics Collection**: Prometheus for scraping model, API, and drift metrics
- **Visualization**: Grafana dashboards for real-time monitoring and drift analysis
- **Drift & Data Quality Monitoring**: Evidently service for distribution drift detection and reports
- **Workflow Orchestration**: Airflow schedules Evidently drift analysis and enforces data-readiness checks
- **Alert Delivery**: Alertmanager receives Prometheus and Airflow task-failure alerts
- **Storage**: MinIO (S3-compatible) for model artifacts
- **Database**: PostgreSQL for MLFlow backend store

**Use Cases:**
- Monitor model performance in production
- Track prediction latency and throughput
- Detect data drift and model degradation
- Compare model versions and A/B testing
- Alert on anomalies and performance issues

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          MONITORING STACK                           │
│                                                                      │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │ Grafana  │─────▶│Prometheus│◀─────│ FastAPI  │                  │
│  │  :3000   │      │  :9090   │      │  :8000   │                  │
│  └──────────┘      └──────────┘      └────┬─────┘                  │
│       ▲                     ▲             │                         │
│       │                     │             │                         │
│       │            ┌────────┴──────┐      │                         │
│       │            │  Evidently    │◀─────┘  (prediction capture)   │
│       │            │  :8001        │  exposes drift/data-quality    │
│       │            └──────────────-┘  metrics to Prometheus         │
│       │                                    │                        │
│       │            ┌──────────┐            │                        │
│       └───────────▶│  MLFlow  │◀───────────┘                        │
│                    │  :5000   │                                     │
│                    └────┬─────┘                                     │
│                         │                                           │
│              ┌──────────┴──────────┐                                │
│              │                     │                                │
│         ┌────▼─────┐         ┌────▼────┐                            │
│         │PostgreSQL│         │  MinIO  │                            │
│         │  :5432   │         │  :9000  │                            │
│         └──────────┘         └─────────┘                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Components

| Service | Port | Description |
|---------|------|-------------|
| **MLFlow** | 5000 | Model registry and experiment tracking |
| **FastAPI** | 8000 | Model serving API with Prometheus metrics |
| **Evidently** | 8001 | Data drift & data-quality monitoring service (Prometheus + HTML reports) |
| **Airflow** | 8080 | Scheduled drift-analysis orchestration |
| **Prometheus** | 9090 | Metrics collection and storage |
| **Alertmanager** | 9093 | Alert grouping, deduplication and delivery |
| **Grafana** | 3000 | Visualization and dashboards (API + drift) |
| **MinIO** | 9000 | S3-compatible object storage for artifacts |
| **MinIO Console** | 9001 | MinIO web interface |
| **PostgreSQL** | 5432 | MLFlow backend database |

---

## Features

### Model Monitoring
- Real-time prediction latency tracking (p50, p95, p99)
- Request throughput and error rate monitoring
- Model version tracking and comparison
- Prediction distribution analysis
- Feature drift detection (via Prometheus + Evidently)

### Metrics Collection
- API request metrics (count, latency, status codes)
- Model prediction metrics (count, latency, errors)
- Feature value distributions for drift detection
- Model load time and version information
- Custom business metrics
- Drift and data-quality metrics from Evidently (drift score, drifted features, missing values)

### Visualization
- Pre-configured Grafana dashboards for API and model metrics
- Dedicated Grafana dashboard for Evidently drift monitoring
- Real-time metric updates
- Alert rules for anomaly and drift detection
- Historical trend analysis
- Multi-model comparison views

### Production Ready
- Docker Compose orchestration
- Health checks for all services
- Automatic MinIO bucket initialization
- Persistent data volumes
- Environment-based configuration

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (≥ 20.10.0)
- **Docker Compose** (≥ 2.0.0)
- **Python** (≥ 3.10) - for model training
---

## Quick Start

### Repository

```bash
unzip ml-monitoring.zip
cd ml-monitoring
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (optional for local development)
nano .env
```

**Default Configuration:**
- User: `dongnd` (used for container naming)
- All passwords: use default for development

###  Start Infrastructure Services

Start all core infrastructure services (PostgreSQL, MinIO, MLFlow, Prometheus, Grafana):

```bash
docker-compose up -d postgres minio minio-init mlflow prometheus grafana
```

**Wait for services to be healthy**:

```bash
# Check service status
docker-compose ps

# All services should show "healthy" or "Up"
```

### ️Train and Register Model

**⚠️ IMPORTANT**: The API requires a trained model in MLFlow Registry before it can start!

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Train and register model
python scripts/training.py
```

**Expected Output:**
```
 MLFlow Tracking URI: http://localhost:5000
  Loading wine dataset...
  Training samples: 142
  Test samples: 36
  Training model...
 Model Performance:
   Accuracy:  0.9722
   F1 Score:  0.9722
   Precision: 0.9750
   Recall:    0.9722
 Model promoted to Production!
   Model: wine_quality_model
   Version: 1
   Stage: Production
```

**What this script does:**
1. Trains a RandomForest classifier on wine dataset
2. Logs model, parameters, and metrics to MLFlow
3. Registers model in MLFlow Model Registry
4. Promotes model to **Production** stage
5. Stores artifacts in MinIO bucket

### Start Model Serving API

Now that the model is registered, start the API:

```bash
docker-compose up -d api
```

**Verify API is running:**

```bash
# Check health
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "model_loaded": true,
#   "model_name": "wine_quality_model",
#   "model_version": "1",
#   "uptime_seconds": 12.34
# }
```

### Start Evidently Drift Service (Optional but Recommended)

Evidently provides drift reports and additional Prometheus metrics:

```bash
docker-compose up -d evidently
```

**Verify Evidently is running:**

```bash
curl http://localhost:8001/health
```

You should see a JSON response with `status: "healthy"`.

### Generate Test Metrics (API & Drift)

Run the helper scripts to generate traffic and metrics:

```bash
# Basic API metrics & Prometheus/Grafana demo
chmod +x test_metrics.sh
./test_metrics.sh

# (Optional) More advanced drift simulations
cd simulations
pip install -r requirements.txt
./quick_test.sh         # small smoke test
python run_simulation.py -n 200 -s moderate_drift --analyze
cd ..
```

These scripts will:
- Send health and prediction requests to the API
- Generate Prometheus metrics for API and model
- Optionally send data to Evidently and trigger drift analysis
- Make it easy to visualize everything in Grafana

### Access Dashboards & UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana (API + Drift)** | http://localhost:3000 | admin / admin |
| **MLFlow** | http://localhost:5000 | - |
| **Prometheus** | http://localhost:9090 | - |
| **MinIO Console** | http://localhost:9001 | minio / minio123 |
| **Evidently API & Reports** | http://localhost:8001 | - (see `/docs`, `/reports`) |
| **API Docs** | http://localhost:8000/docs | - |

---

## Configuration

### Environment Variables

All configuration is managed through the `.env` file:

```bash
# User Configuration
USER=dongnd                    # Your username (for container naming)

# MLFlow Configuration
MLFLOW_PORT=5000              # MLFlow server port
MODEL_NAME=wine_quality_model # Model name in registry
MODEL_STAGE=Production        # Model stage to serve

# MinIO Configuration
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123 
MINIO_BUCKET_NAME=mlflow-artifacts

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# See .env.example for all options
```

### Grafana Datasource

The Prometheus datasource is automatically provisioned with:
- **UID**: `prometheus-datasource` (stable reference)
- **URL**: `http://prometheus:9090`
- **Query Timeout**: 60s
- **HTTP Method**: POST (faster queries)
- **Incremental Querying**: Enabled

---

## Training Models

### Using the Training Script

The included training script (`scripts/training.py`) trains a RandomForest model on the wine dataset:

```bash
# Basic usage
python scripts/training.py
```

### Training Your Own Models

To train your own models:

1. **Create a training script** following this pattern:

```python
import mlflow
import mlflow.sklearn
import os

# Configure MLFlow
mlflow.set_tracking_uri('http://localhost:5000')
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'

# Train your model
with mlflow.start_run(run_name="my_model_v1"):
    # ... train model ...
    
    # Log model
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="my_model",
        signature=mlflow.models.infer_signature(X_train, predictions)
    )
    
    run_id = mlflow.active_run().info.run_id

# Promote to Production
client = mlflow.tracking.MlflowClient()
model_versions = client.get_latest_versions("my_model", stages=["None"])
if model_versions:
    client.transition_model_version_stage(
        name="my_model",
        version=model_versions[0].version,
        stage="Production"
    )
```

2. **Update environment variables** in `docker-compose.yml`:

```yaml
api:
  environment:
    - MODEL_NAME=my_model 
    - MODEL_STAGE=Production
```

3. **Restart the API**:

```bash
docker-compose restart api
```

### Model Requirements

Your model must:
- Be registered in MLFlow Model Registry
- Have a version promoted to the specified stage (default: Production)
- Be compatible with `mlflow.pyfunc.load_model()`
- Accept numeric array input for predictions

---

## Monitoring & Dashboards

### Accessing Grafana

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Navigate to **Dashboards** → **ML Monitoring** (API/model metrics)
4. Navigate to **Dashboards** → **Evidently - Data Drift Monitoring** (drift metrics)

### Available Metrics

The API exposes these Prometheus metrics at `http://localhost:8000/metrics`:

#### API Metrics
```promql
# Request count by method, endpoint, and status
api_requests_total{method="POST",endpoint="/predict",status="200"}

# Request latency histogram
api_request_latency_seconds{method="POST",endpoint="/predict"}
```

#### Model Metrics
```promql
# Prediction count by model and version
model_predictions_total{model_name="wine_quality_model",model_version="1"}

# Prediction latency histogram
model_prediction_latency_seconds{model_name="wine_quality_model"}

# Prediction value distribution (for drift detection)
model_prediction_value{model_name="wine_quality_model"}

# Prediction errors by type
model_prediction_errors_total{model_name="wine_quality_model",error_type="..."}
```

#### System Metrics
```promql
# Current model version
model_version_info{model_name="wine_quality_model",version="1"}

# Model load time
model_load_time_seconds{model_name="wine_quality_model"}
```

### Example Queries

```promql
# Requests per second
rate(api_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(model_prediction_latency_seconds_bucket[5m]))

# Error rate
rate(model_prediction_errors_total[5m]) / rate(model_predictions_total[5m])

# Average prediction value (drift detection)
rate(model_prediction_value_sum[5m]) / rate(model_prediction_value_count[5m])
```

---

## Evidently & Drift Monitoring

Evidently runs as a separate service (port **8001**) and provides:

- **REST API** for capturing prediction data and triggering analysis
- **HTML reports** for detailed drift and data-quality inspection
- **Prometheus metrics** used by the Grafana drift dashboard

### Key Endpoints

- `GET /health` – service health and summary
- `POST /capture` – capture a single prediction (features + prediction)
- `POST /capture/batch` – capture a batch of predictions
- `POST /analyze` – run drift analysis on recent production data
- `GET /reports` – list available HTML drift reports
- `GET /reports/{name}` – view a specific report
- `GET /metrics` – Prometheus metrics (e.g. `evidently_data_drift_detected`, `evidently_drift_score`)

### Typical Drift Monitoring Flow

1. The **API** serves predictions and exposes metrics at `/metrics`.
2. A **simulation script** (or your real app) sends traffic to `/predict`.
3. The simulator optionally **captures** each request/response to Evidently (`/capture`).
4. On a schedule (or manually), Evidently `/analyze` compares recent production data with reference data and:
   - Updates Prometheus metrics (drift status, scores, drifted features, missing values, etc.).
   - Generates an HTML drift report.
5. **Prometheus** scrapes Evidently, and **Grafana** dashboards visualize drift and data quality.

### Drift Dashboard in Grafana

- Dashboard UID: `evidently-drift`
- File: `config/grafana/dashboards/evidently-drift-monitoring.json`
- Shows:
  - Current drift status and drifted-features count
  - Drift score over time
  - Feature-level drift matrix
  - Analysis latency and rate
  - Missing-values ratio per feature

### Alerts

Prometheus alert rules for Evidently are defined in:

- `config/prometheus/evidently_alerts.yml`

Examples:

- `DataDriftDetected` – drift detected for ≥ 5 minutes
- `MultipleDriftedFeatures` – 3+ features drifting
- `HighDriftScore` – drift score > 0.5
- `HighMissingValues` – missing-values ratio > 20%
- `SlowDriftAnalysis` – analysis taking too long

These alerts are delivered to Alertmanager by default.

---

## Airflow & Alerting

Airflow runs the `model_drift_monitoring` DAG every 15 minutes. The DAG first checks that
Evidently has reference data and at least 100 production samples; it is marked **skipped**
until those prerequisites exist, rather than producing a false failure. When ready, it calls
Evidently's `/analyze` endpoint.

Each task has one retry. After the retry is exhausted, its failure callback posts an
`AirflowTaskFailed` alert directly to Alertmanager. This is intentionally direct, so an
Airflow task error is visible immediately instead of waiting for the next Prometheus scrape.

### Start the Services

Set a non-default Airflow admin password and a unique Fernet key in `.env` before a shared or
production deployment. For local learning, the values in `.env.example` work.

```bash
# Generate a Fernet key, then paste it into AIRFLOW_FERNET_KEY in .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Build the Airflow image and start orchestration, metrics and alerting.
docker compose up -d --build \
  evidently alert-receiver alertmanager statsd-exporter \
  airflow-webserver airflow-scheduler
```

The first start also creates the `airflow` PostgreSQL database and the Airflow admin account.

| Service | URL | Default credentials |
|---|---|---|
| Airflow | http://localhost:8080 | `admin` / `admin` |
| Alertmanager | http://localhost:9093 | - |
| StatsD Exporter metrics | http://localhost:9102/metrics | - |

### Metrics and Alert Rules

Airflow sends StatsD metrics to StatsD Exporter; Prometheus scrapes them as
`airflow-metrics`. Airflow uses the StatsD InfluxDB tag format so DAG and task identifiers
are retained as Prometheus labels; selected metrics are mapped in `config/statsd_mapping.yml`.

- `AirflowMetricsExporterDown` - StatsD Exporter cannot be scraped for two minutes.
- `AirflowSchedulerHeartbeatMissing` - no scheduler heartbeat for at least five minutes.
- `AirflowDagImportErrors` - a DAG cannot be imported.
- `AirflowTaskFailed` - immediate Alertmanager event posted by the DAG failure callback.

The local receiver logs every delivery. To relay the raw Alertmanager payload to an external
generic webhook, set `ALERT_WEBHOOK_URL` in `.env` and restart `alert-receiver`.

```bash
docker compose logs -f alert-receiver
```

### Test an Alert Safely

The DAG supports a manual test flag, so it does not require intentionally breaking code:

```bash
docker compose exec airflow-scheduler airflow dags trigger model_drift_monitoring \
  --conf '{"force_failure": true}'

# The receiver logs the alert immediately; it is also visible in Alertmanager.
docker compose logs -f alert-receiver
```

---

## Simulations & Load Testing

To generate realistic traffic and drift scenarios, use the tools in the `simulations/` directory.

### Installation

```bash
cd simulations
pip install -r requirements.txt
```

### Quick Test

```bash
cd simulations
./quick_test.sh       # 20 quick requests to validate everything end-to-end
cd ..
```

### CLI Usage

```bash
cd simulations

# 100 normal requests at 2 req/s
python run_simulation.py -n 100 -s normal

# 200 requests with moderate drift + run Evidently analysis
python run_simulation.py -n 200 -s moderate_drift --analyze

# Burst traffic pattern
python run_simulation.py -p burst -s normal

# Gradual traffic increase
python run_simulation.py -p gradual -s normal
```

### Pre‑configured Scenarios

```bash
cd simulations

# Run a specific scenario
python scenarios.py 1  # Normal day traffic
python scenarios.py 2  # Gradual drift
python scenarios.py 3  # Sudden distribution shift
python scenarios.py 6  # Stress test

# Run all scenarios sequentially (demo)
python scenarios.py
```

These simulations:

- Hit the `/predict` endpoint on the API.
- Optionally **capture** each prediction to Evidently.
- Automatically **feed** metrics and drift signals into Prometheus & Grafana.

---

## API Documentation

### Endpoints

#### `GET /`
Root endpoint with API information.

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "wine_quality_model",
  "model_version": "1",
  "uptime_seconds": 123.45
}
```

#### `POST /predict`
Make predictions with the loaded model.

**Request:**
```json
{
  "features": [13.64, 3.1, 2.56, 15.2, 116.0, 2.7, 3.03, 0.17, 1.66, 5.1, 0.96, 3.36, 845.0],
  "feature_names": ["fixed_acidity", "volatile_acidity", ...] // optional
}
```

**Response:**
```json
{
  "prediction": 1.0,
  "model_name": "wine_quality_model",
  "model_version": "1",
  "timestamp": "2025-11-19T12:00:00",
  "latency_ms": 15.23
}
```

#### `GET /model/info`
Get loaded model information.

#### `POST /model/reload`
Reload model from registry.

#### `GET /metrics`
Prometheus metrics endpoint.

### Interactive API Docs

Access Swagger UI at: http://localhost:8000/docs

---

## Troubleshooting

### Common Issues

#### 1. API fails to start: "Model not loaded"

**Problem**: No model registered in MLFlow or wrong model name/stage.

**Solution:**
```bash
# Check if model exists
curl http://localhost:5000/api/2.0/mlflow/registered-models/get?name=wine_quality_model

# Train and register model
python scripts/training.py

# Restart API
docker-compose restart api
```

#### 2. MLFlow healthcheck failing

**Problem**: Port mismatch or MLFlow not ready.

**Solution:**
```bash
# Check MLFlow logs
docker-compose logs mlflow

# Verify port (should be 5000)
docker-compose ps mlflow

# Restart if needed
docker-compose restart mlflow
```

#### 3. MinIO bucket not created

**Problem**: minio-init service failed.

**Solution:**
```bash
# Check init logs
docker-compose logs minio-init

# Manual bucket creation
docker-compose exec minio mc alias set myminio http://localhost:9000 minio minio123
docker-compose exec minio mc mb myminio/mlflow-artifacts --ignore-existing
```

#### 4. Grafana datasource not working

**Problem**: Prometheus not accessible or wrong configuration.

**Solution:**
```bash
# Test Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana datasource
# Go to: http://localhost:3000/datasources
# Click Prometheus → Test

# Verify configuration in:
cat config/grafana/provisioning/datasources/prometheus.yml
```

### Service Health Checks

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f mlflow
docker-compose logs -f api
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f airflow-scheduler
docker-compose logs -f alert-receiver

# Test endpoints
curl http://localhost:5000/health    # MLFlow
curl http://localhost:8000/health    # API
curl http://localhost:9090/-/healthy # Prometheus
curl http://localhost:3000/api/health # Grafana
curl http://localhost:8080/health     # Airflow webserver
curl http://localhost:9093/-/healthy  # Alertmanager
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove volumes (️deletes all data!)
docker-compose down -v

# Rebuild and start fresh
docker-compose build
docker-compose up -d postgres minio minio-init mlflow prometheus grafana

# Train model again
python scripts/training.py

# Start API
docker-compose up -d api
```

---

## Project Structure

```
ml-monitoring/
├── api/                          # FastAPI model serving
│   ├── Dockerfile
│   ├── main.py                   # API application with metrics
│   └── requirements.txt
├── mlflow/                       # MLFlow server
│   └── Dockerfile
├── airflow/                       # Airflow image extension (StatsD client)
│   └── Dockerfile
├── airflow_dags/
│   └── model_monitoring.py        # Scheduled Evidently analysis + failure callback
├── alert_receiver/                # Local Alertmanager webhook receiver
│   ├── Dockerfile
│   └── main.py
├── config/                       # Configuration files
│   ├── prometheus.yml            # Prometheus scrape config
│   ├── alertmanager/
│   │   └── alertmanager.yml       # Alert routing config
│   ├── prometheus/
│   │   ├── airflow_alerts.yml     # Airflow health alert rules
│   │   └── evidently_alerts.yml   # Evidently alert rules
│   ├── statsd_mapping.yml         # Airflow-to-Prometheus metric mapping
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/      # Grafana datasources
│       │   │   └── prometheus.yml
│       │   └── dashboards/       # Dashboard provisioning
│       │       └── dashboards.yml
│       ├── dashboards/           # Dashboard JSON files
│       │   └── ml-monitoring.json
│       └── alerts.yml            # Alert rules
├── scripts/                      # Training and utility scripts
│   ├── training.py               # Model training script
│   └── requirements.txt
├── docker-compose.yml            # Main orchestration file
├── .env.example                  # Environment template
├── .env                          # Active environment config
└── README.md                     # This file
```

---

## 📄 License

This project is provided as-is for demonstration purposes.
