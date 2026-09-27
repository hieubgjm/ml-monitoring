from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import mlflow
import mlflow.pyfunc
import numpy as np
import time
import logging
from datetime import datetime
import os

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# ============================================
# CONFIGURATION
# ============================================

MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MODEL_NAME = os.getenv('MODEL_NAME', 'wine_quality_model')
MODEL_STAGE = os.getenv('MODEL_STAGE', 'Production')  # Production, Staging, None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# PROMETHEUS METRICS
# ============================================

# Request metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Prediction metrics
PREDICTION_COUNT = Counter(
    'model_predictions_total',
    'Total predictions made',
    ['model_name', 'model_version']
)

PREDICTION_LATENCY = Histogram(
    'model_prediction_latency_seconds',
    'Model prediction latency',
    ['model_name'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Model metrics
CURRENT_MODEL_VERSION = Gauge(
    'model_version_info',
    'Current model version',
    ['model_name', 'version']
)

MODEL_LOAD_TIME = Gauge(
    'model_load_time_seconds',
    'Time taken to load model',
    ['model_name']
)

# Prediction distribution (for drift detection)
PREDICTION_VALUE = Histogram(
    'model_prediction_value',
    'Distribution of prediction values',
    ['model_name'],
    buckets=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # For wine quality 0-10
)

# Error metrics
PREDICTION_ERRORS = Counter(
    'model_prediction_errors_total',
    'Total prediction errors',
    ['model_name', 'error_type']
)

# Feature metrics (for drift detection)
FEATURE_VALUE = Histogram(
    'model_feature_value',
    'Distribution of feature values',
    ['feature_name'],
    buckets=np.linspace(-3, 3, 20).tolist()  # Standardized features
)

# ============================================
# PYDANTIC MODELS
# ============================================

class PredictionRequest(BaseModel):
    """Request model for prediction"""
    features: List[float] = Field(..., description="List of feature values")
    feature_names: Optional[List[str]] = Field(None, description="Feature names (optional)")
    
    class Config:
        schema_extra = {
            "example": {
                "features": [7.4, 0.7, 0.0, 1.9, 0.076, 11.0, 34.0, 0.9978, 3.51, 0.56, 9.4],
                "feature_names": ["fixed_acidity", "volatile_acidity", "citric_acid", ...]
            }
        }

class PredictionResponse(BaseModel):
    """Response model for prediction"""
    prediction: float
    model_name: str
    model_version: str
    timestamp: str
    latency_ms: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    model_name: str
    model_version: str
    uptime_seconds: float

# ============================================
# MODEL MANAGER
# ============================================

class ModelManager:
    """Manage ML model from MLFlow Registry"""
    
    def __init__(self):
        self.model = None
        self.model_name = MODEL_NAME
        self.model_version = None
        self.model_uri = None
        self.load_time = None
        
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        logger.info(f"MLFlow tracking URI: {MLFLOW_TRACKING_URI}")
    
    def load_model(self):
        """Load model from MLFlow Registry"""
        try:
            start_time = time.time()
            
            # Get model URI from registry
            if MODEL_STAGE:
                # Load by stage (Production, Staging)
                self.model_uri = f"models:/{self.model_name}/{MODEL_STAGE}"
                logger.info(f"Loading model: {self.model_name} (Stage: {MODEL_STAGE})")
            else:
                # Load latest version
                self.model_uri = f"models:/{self.model_name}/latest"
                logger.info(f"Loading model: {self.model_name} (Latest)")
            
            # Load model
            self.model = mlflow.pyfunc.load_model(self.model_uri)
            
            # Get model version
            client = mlflow.tracking.MlflowClient()
            model_versions = client.get_latest_versions(self.model_name, stages=[MODEL_STAGE] if MODEL_STAGE else None)
            
            if model_versions:
                self.model_version = model_versions[0].version
            else:
                self.model_version = "unknown"
            
            self.load_time = time.time() - start_time
            
            # Update Prometheus metrics
            CURRENT_MODEL_VERSION.labels(
                model_name=self.model_name,
                version=self.model_version
            ).set(int(self.model_version) if self.model_version.isdigit() else 0)
            
            MODEL_LOAD_TIME.labels(model_name=self.model_name).set(self.load_time)
            
            logger.info(f"   Model loaded successfully!")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Version: {self.model_version}")
            logger.info(f"   Load time: {self.load_time:.2f}s")
            
            return True
        
        except Exception as e:
            logger.error(f" Failed to load model: {e}")
            PREDICTION_ERRORS.labels(
                model_name=self.model_name,
                error_type='model_load_error'
            ).inc()
            return False
    
    def predict(self, features: List[float]) -> float:
        """Make prediction"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Convert to numpy array
        features_array = np.array(features).reshape(1, -1)
        
        # Predict
        start_time = time.time()
        prediction = self.model.predict(features_array)
        latency = time.time() - start_time
        
        # Update metrics
        PREDICTION_COUNT.labels(
            model_name=self.model_name,
            model_version=self.model_version
        ).inc()
        
        PREDICTION_LATENCY.labels(
            model_name=self.model_name
        ).observe(latency)
        
        # Track prediction distribution
        pred_value = float(prediction[0])
        PREDICTION_VALUE.labels(
            model_name=self.model_name
        ).observe(pred_value)
        
        return pred_value, latency

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="ML Model API",
    description="Production ML model serving with monitoring",
    version="1.0.0"
)

# Initialize model manager
model_manager = ModelManager()
app_start_time = time.time()

# ============================================
# MIDDLEWARE - REQUEST TRACKING
# ============================================

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all requests with Prometheus"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency = time.time() - start_time
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(latency)
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} latency={latency:.3f}s"
    )
    
    return response

# ============================================
# STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    logger.info("Starting API server...")
    
    success = model_manager.load_model()
    
    if not success:
        logger.error("Failed to load model on startup")
        # In production, you might want to exit here
        # raise RuntimeError("Model load failed")
    else:
        logger.info("API server ready!")

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ML Model API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "metrics": "/metrics",
            "model_info": "/model/info"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time
    
    return HealthResponse(
        status="healthy" if model_manager.model is not None else "unhealthy",
        model_loaded=model_manager.model is not None,
        model_name=model_manager.model_name,
        model_version=model_manager.model_version or "unknown",
        uptime_seconds=uptime
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Prediction endpoint"""
    try:
        # Check if model is loaded
        if model_manager.model is None:
            PREDICTION_ERRORS.labels(
                model_name=model_manager.model_name,
                error_type='model_not_loaded'
            ).inc()
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Track feature distributions (for drift detection)
        if request.feature_names and len(request.feature_names) == len(request.features):
            for fname, fvalue in zip(request.feature_names, request.features):
                FEATURE_VALUE.labels(feature_name=fname).observe(fvalue)
        
        # Make prediction
        start_time = time.time()
        prediction, pred_latency = model_manager.predict(request.features)
        total_latency = time.time() - start_time
        
        return PredictionResponse(
            prediction=prediction,
            model_name=model_manager.model_name,
            model_version=model_manager.model_version,
            timestamp=datetime.now().isoformat(),
            latency_ms=total_latency * 1000
        )
    
    except ValueError as e:
        PREDICTION_ERRORS.labels(
            model_name=model_manager.model_name,
            error_type='value_error'
        ).inc()
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        PREDICTION_ERRORS.labels(
            model_name=model_manager.model_name,
            error_type='unknown_error'
        ).inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@app.get("/model/info")
async def model_info():
    """Get model information"""
    if model_manager.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_name": model_manager.model_name,
        "model_version": model_manager.model_version,
        "model_uri": model_manager.model_uri,
        "load_time_seconds": model_manager.load_time,
        "tracking_uri": MLFLOW_TRACKING_URI
    }

@app.post("/model/reload")
async def reload_model():
    """Reload model from registry"""
    logger.info(" Reloading model...")
    
    success = model_manager.load_model()
    
    if success:
        return {
            "status": "success",
            "message": "Model reloaded successfully",
            "model_version": model_manager.model_version
        }
    else:
        raise HTTPException(status_code=500, detail="Model reload failed")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable in production
        log_level="info"
    )