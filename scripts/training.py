"""
============================================
TRAIN & REGISTER MODEL TO MLFLOW
============================================

This script:
1. Trains a simple model
2. Logs to MLFlow
3. Registers to MLFlow Model Registry
4. Promotes to Production stage
"""

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import numpy as np
import os

# ============================================
# CONFIGURATION
# ============================================

MLFLOW_TRACKING_URI = 'http://localhost:5000'
MODEL_NAME = "wine_quality_model"
EXPERIMENT_NAME = "wine_quality_experiment"

# Configure MinIO S3 for artifacts
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
os.environ['MLFLOW_S3_IGNORE_TLS'] = 'true'

print(f"🔧 MLFlow Tracking URI: {MLFLOW_TRACKING_URI}")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# ============================================
# LOAD DATA
# ============================================

print("📊 Loading wine dataset...")
wine = load_wine()
X, y = wine.data, wine.target

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Training samples: {len(X_train)}")
print(f"   Test samples: {len(X_test)}")

# ============================================
# TRAIN MODEL
# ============================================

print("\n🎯 Training model...")

# Set experiment
mlflow.set_experiment(EXPERIMENT_NAME)

print(f"🎯 Experiment: {EXPERIMENT_NAME}")

# Start MLFlow run
with mlflow.start_run(run_name="RandomForest_v1") as run:
    
    # Hyperparameters
    params = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 2,
        'random_state': 42
    }
    
    # Train model
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    
    print(f"\n📈 Model Performance:")
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   F1 Score:  {f1:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    
    # Log parameters
    mlflow.log_params(params)
    
    # Log metrics
    mlflow.log_metrics({
        'accuracy': accuracy,
        'f1_score': f1,
        'precision': precision,
        'recall': recall
    })
    
    # Log model
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name=MODEL_NAME,
        signature=mlflow.models.infer_signature(X_train, y_pred),
        input_example=X_train[:5]
    )
    
    run_id = run.info.run_id
    print(f"\n Model logged to MLFlow!")
    print(f"   Run ID: {run_id}")

# ============================================
# PROMOTE TO PRODUCTION
# ============================================

print("\n Promoting model to Production stage...")

client = mlflow.tracking.MlflowClient()

# Get latest version
model_versions = client.get_latest_versions(MODEL_NAME, stages=["None"])

if model_versions:
    latest_version = model_versions[0].version
    
    # Transition to Production
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=latest_version,
        stage="Production",
        archive_existing_versions=True  # Archive old production versions
    )
    
    print(f"✅ Model promoted to Production!")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Version: {latest_version}")
    print(f"   Stage: Production")
else:
    print("❌ No model versions found")

# ============================================
# SUMMARY
# ============================================

print("\n" + "="*50)
print(" SETUP COMPLETE!")
print("="*50)
print(f"\n Next steps:")
print(f"   1. Start API: docker-compose up -d api")
print(f"   2. Test API: curl http://localhost:8000/health")
print(f"   3. Make prediction: curl -X POST http://localhost:8000/predict \\")
print(f"      -H 'Content-Type: application/json' \\")
print(f"      -d '{{'features': {X_test[0].tolist()}}}'")
print(f"   4. View metrics: http://localhost:8000/metrics")
print(f"   5. View Grafana: http://localhost:3000")
print(f"   6. View MLFlow: http://localhost:5000")
print()