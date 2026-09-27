# 🎮 ML Model Prediction Simulator

Professional simulation tools for testing ML monitoring system with realistic traffic patterns and drift scenarios.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Scenarios](#scenarios)
- [Configuration](#configuration)
- [Examples](#examples)

---

## 🎯 Overview

This simulation toolkit allows you to:
- Generate realistic wine quality prediction requests
- Simulate various data drift scenarios
- Test monitoring dashboards and alerts
- Stress test API performance
- Validate drift detection accuracy

---

## ✨ Features

### Data Generation
- ✅ Realistic wine dataset simulation
- ✅ Configurable feature distributions
- ✅ 5 drift scenarios (normal to severe)
- ✅ Customizable noise levels

### Traffic Patterns
- ✅ Steady traffic flow
- ✅ Burst traffic spikes
- ✅ Gradually increasing load
- ✅ Custom RPS configuration

### Integration
- ✅ Auto-capture to Evidently AI
- ✅ Trigger drift analysis
- ✅ Real-time metrics exposure
- ✅ Grafana dashboard updates

### Scenarios
- ✅ 6 pre-configured scenarios
- ✅ Normal day simulation
- ✅ Gradual drift introduction
- ✅ Sudden distribution shifts
- ✅ Mixed conditions
- ✅ Stress testing

---

## 📦 Installation

### Step 1: Install Dependencies

```bash
cd simulations
pip install -r requirements.txt
```

### Step 2: Verify Services

Ensure these services are running:
```bash
docker-compose ps

# Should show:
# - api (port 8000)
# - evidently (port 8001)
# - prometheus (port 9090)
# - grafana (port 3000)
```

### Step 3: Test Connection

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

## 🚀 Quick Start

### Option 1: Use CLI Tool

```bash
# Basic simulation
python run_simulation.py --requests 100 --scenario normal

# With custom RPS
python run_simulation.py --requests 200 --rps 5 --scenario moderate_drift

# Use traffic pattern
python run_simulation.py --pattern burst --scenario severe_drift

# Run and analyze
python run_simulation.py --requests 100 --analyze --window 100
```

### Option 2: Run Pre-configured Scenarios

```bash
# Run specific scenario
python scenarios.py 1  # Normal day
python scenarios.py 2  # Gradual drift
python scenarios.py 3  # Sudden shift

# Run all scenarios
python scenarios.py
```

### Option 3: Use Python API

```python
from simulator import PredictionSimulator

# Initialize
sim = PredictionSimulator()

# Run simulation
sim.run_simulation(
    n_requests=100,
    scenario="moderate_drift",
    requests_per_second=5,
    capture_to_evidently=True
)

# Analyze drift
sim.trigger_drift_analysis(window_size=100)
```

---

## 📖 Usage

### CLI Tool: `run_simulation.py`

```bash
python run_simulation.py [OPTIONS]

Options:
  -n, --requests INT        Number of requests (default: 100)
  -d, --duration INT        Duration in seconds (overrides --requests)
  -r, --rps FLOAT          Requests per second (default: 2.0)
  -s, --scenario CHOICE    Scenario: normal, slight_drift, moderate_drift,
                           severe_drift, sudden_shift (default: normal)
  -p, --pattern CHOICE     Traffic pattern: burst, steady, gradual
  --no-capture             Don't capture to Evidently
  --analyze                Trigger drift analysis after completion
  --window INT             Analysis window size (default: 100)
  -q, --quiet              Quiet mode (no progress bar)
  --config PATH            Config file (default: config.yaml)
```

### Scenarios: `scenarios.py`

```bash
python scenarios.py [SCENARIO_NUMBER]

Scenarios:
  1  Normal Day          - 8 hours of steady traffic
  2  Gradual Drift       - Drift gradually increases
  3  Sudden Shift        - Abrupt distribution change
  4  Traffic Spike       - Burst pattern simulation
  5  Mixed Conditions    - Alternating normal/drift
  6  Stress Test         - High-volume traffic

  (no args)              - Run all scenarios
```

---

## 🎭 Scenarios

### 1. Normal Day (`scenario="normal"`)
- **Description**: Realistic normal operating conditions
- **Drift**: None
- **Use Case**: Baseline testing, dashboard verification

### 2. Slight Drift (`scenario="slight_drift"`)
- **Description**: Minor drift in 2-3 features
- **Drift Multiplier**: 1.2x
- **Use Case**: Early drift detection testing

### 3. Moderate Drift (`scenario="moderate_drift"`)
- **Description**: Noticeable drift in 3-5 features
- **Drift Multiplier**: 1.5x
- **Use Case**: Alert threshold tuning

### 4. Severe Drift (`scenario="severe_drift"`)
- **Description**: Significant drift in most features
- **Drift Multiplier**: 2.0x
- **Use Case**: Critical alert testing

### 5. Sudden Shift (`scenario="sudden_shift"`)
- **Description**: Extreme distribution change
- **Drift Multiplier**: 2.5x
- **Use Case**: Worst-case scenario testing

---

## ⚙️ Configuration

### File: `config.yaml`

```yaml
# API Endpoints
api:
  prediction_url: "http://localhost:8000/predict"
  evidently_capture_url: "http://localhost:8001/capture"

# Feature Distributions
features:
  feature_name:
    min: 0.0
    max: 10.0
    mean: 5.0
    std: 1.0

# Scenarios
scenarios:
  custom_scenario:
    drift_multiplier: 1.5
    noise_level: 0.2
    affected_features: 3

# Traffic Patterns
traffic:
  custom_pattern:
    requests_per_second: 5
    duration_seconds: 120
```

---

## 💡 Examples

### Example 1: Basic Testing

```bash
# Test normal traffic
python run_simulation.py -n 50 -s normal -r 2

# Test with drift
python run_simulation.py -n 50 -s moderate_drift -r 2

# Analyze results
python run_simulation.py -n 100 --analyze
```

### Example 2: Dashboard Testing

```bash
# Generate continuous traffic for 5 minutes
python run_simulation.py -d 300 -r 2 -s normal

# Watch Grafana dashboard update in real-time
# http://localhost:3000/d/evidently-drift
```

### Example 3: Drift Detection Testing

```bash
# Phase 1: Normal baseline
python run_simulation.py -n 100 -s normal

# Phase 2: Introduce drift
python run_simulation.py -n 100 -s severe_drift --analyze

# Check alerts in Prometheus
# http://localhost:9090/alerts
```

### Example 4: Stress Testing

```bash
# High RPS test
python run_simulation.py -d 60 -r 20 -s normal

# Burst pattern
python run_simulation.py -p burst -s normal

# Monitor performance metrics in Grafana
```

### Example 5: Automated Testing

```python
# test_drift_detection.py
from simulator import PredictionSimulator
import time

sim = PredictionSimulator()

# Establish baseline
print("Establishing baseline...")
sim.run_simulation(n_requests=200, scenario="normal")
time.sleep(5)

# Introduce drift
print("Introducing drift...")
sim.run_simulation(n_requests=200, scenario="severe_drift")

# Analyze
result = sim.trigger_drift_analysis(window_size=300)

# Assert drift detected
assert result['drift_detected'], "Drift should be detected!"
print("✓ Drift detection working correctly")
```

---

## 📊 Monitoring Integration

### Grafana Dashboard

While simulation runs:
1. Open: http://localhost:3000/d/evidently-drift
2. Watch panels update in real-time
3. Observe metrics:
   - API request count
   - Prediction latency
   - Drift detection status
   - Feature drift matrix

### Prometheus Metrics

Query during simulation:
```promql
# Request rate
rate(api_requests_total[1m])

# Prediction count
rate(model_predictions_total[1m])

# Drift status
evidently_data_drift_detected

# Drifted features
evidently_drifted_features_count
```

### Evidently Reports

After simulation with drift:
```bash
# List reports
curl http://localhost:8001/reports

# View latest report
open http://localhost:8001/reports/drift_report_YYYYMMDD_HHMMSS.html
```

---

## 🔧 Advanced Usage

### Custom Data Generator

```python
from data_generator import WineDataGenerator

gen = WineDataGenerator()

# Generate custom batch
samples = gen.generate_batch(
    n_samples=100,
    scenario="custom"
)

# Generate with specific drift
drifted = gen.generate_drifted_sample(
    drift_multiplier=2.0,
    affected_features=['alcohol', 'pH', 'density'],
    noise_level=0.3
)
```

### Custom Traffic Pattern

```python
from simulator import PredictionSimulator

sim = PredictionSimulator()

# Implement custom pattern
for i in range(10):
    rps = 1 + i  # Gradually increase
    sim.run_simulation(
        n_requests=int(rps * 10),
        scenario="normal" if i < 5 else "moderate_drift",
        requests_per_second=rps
    )
```

### Batch Analysis

```python
# Run multiple simulations and collect results
results = []

for scenario in ["normal", "slight_drift", "moderate_drift"]:
    sim = PredictionSimulator()
    sim.run_simulation(n_requests=100, scenario=scenario)
    result = sim.trigger_drift_analysis(window_size=100)
    results.append({
        'scenario': scenario,
        'drift_detected': result['drift_detected'],
        'drift_score': result['drift_score']
    })

# Analyze results
import pandas as pd
df = pd.DataFrame(results)
print(df)
```

---

## 🐛 Troubleshooting

### Issue: Connection Refused

```bash
# Check services
docker-compose ps

# Restart if needed
docker-compose restart api evidently

# Verify
curl http://localhost:8000/health
```

### Issue: Import Errors

```bash
# Ensure in simulations directory
cd simulations

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version (>= 3.10)
python --version
```

### Issue: Slow Performance

```bash
# Reduce RPS
python run_simulation.py -r 1

# Disable Evidently capture
python run_simulation.py --no-capture

# Use quiet mode
python run_simulation.py -q
```

---

## 📚 Project Structure

```
simulations/
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── data_generator.py        # Data generation logic
├── simulator.py             # Core simulation engine
├── run_simulation.py        # CLI tool
├── scenarios.py             # Pre-configured scenarios
└── README.md               # This file
```

---

## 🎯 Use Cases

### 1. **Development Testing**
```bash
# Quick functional test
python run_simulation.py -n 10 -s normal
```

### 2. **Dashboard Validation**
```bash
# Generate traffic for dashboard testing
python run_simulation.py -d 300 -r 2
```

### 3. **Drift Detection Testing**
```bash
# Test drift detection
python scenarios.py 2  # Gradual drift
```

### 4. **Performance Testing**
```bash
# Stress test
python scenarios.py 6
```

### 5. **Alert Testing**
```bash
# Trigger alerts
python run_simulation.py -n 200 -s severe_drift --analyze
```

### 6. **Demo / Presentation**
```bash
# Run all scenarios for demo
python scenarios.py
```

---

## 🔗 Related Documentation

- **Main README**: `../README.md`
- **Evidently Guide**: `../EVIDENTLY_QUICKSTART.md`
- **Grafana Dashboard**: `../GRAFANA_DRIFT_DASHBOARD.md`
- **API Documentation**: http://localhost:8000/docs

---

## 📝 Quick Reference

```bash
# Most common commands

# Basic test
python run_simulation.py -n 100

# With drift
python run_simulation.py -n 100 -s moderate_drift

# High traffic
python run_simulation.py -r 10 -d 60

# Analyze drift
python run_simulation.py -n 200 --analyze

# Pre-configured scenario
python scenarios.py 2

# All scenarios
python scenarios.py
```

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Python**: ≥ 3.10  
**Dependencies**: See `requirements.txt`

