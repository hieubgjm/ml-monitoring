"""
============================================
PREDICTION SIMULATOR
============================================

Simulate prediction requests to API and capture to Evidently
"""

import requests
import time
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from tqdm import tqdm
from colorama import Fore, Style, init
import yaml
import json
import logging
from pathlib import Path

from data_generator import WineDataGenerator

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionSimulator:
    """Simulate prediction traffic"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize simulator"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.api_config = self.config['api']
        self.data_generator = WineDataGenerator(config_path)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0.0,
            'predictions': [],
            'errors': []
        }
    
    def check_api_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(
                self.api_config['health_url'],
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ API is healthy: {data.get('status', 'unknown')}")
                logger.info(f"  Model: {data.get('model_name', 'N/A')} v{data.get('model_version', 'N/A')}")
                return True
            else:
                logger.error(f"✗ API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Cannot reach API: {e}")
            return False
    
    def send_prediction(
        self,
        features: Dict[str, float],
        capture_to_evidently: bool = True
    ) -> Optional[Dict]:
        """Send single prediction request"""
        
        try:
            # Prepare request
            payload = {
                "features": list(features.values()),
                "feature_names": list(features.keys())
            }
            
            # Send prediction request
            start_time = time.time()
            response = requests.post(
                self.api_config['prediction_url'],
                json=payload,
                timeout=10
            )
            latency = time.time() - start_time
            
            # Update stats
            self.stats['total_requests'] += 1
            self.stats['total_latency'] += latency
            
            if response.status_code == 200:
                result = response.json()
                self.stats['successful_requests'] += 1
                self.stats['predictions'].append(result['prediction'])
                
                # Capture to Evidently if enabled
                if capture_to_evidently:
                    self._capture_to_evidently(features, result['prediction'])
                
                return {
                    'success': True,
                    'prediction': result['prediction'],
                    'latency': latency,
                    'model_version': result.get('model_version', 'unknown')
                }
            else:
                self.stats['failed_requests'] += 1
                self.stats['errors'].append(response.text)
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.stats['errors'].append(str(e))
            logger.error(f"Prediction error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _capture_to_evidently(self, features: Dict[str, float], prediction: float):
        """Capture data to Evidently"""
        try:
            payload = {
                "features": features,
                "prediction": prediction,
                "timestamp": datetime.now().isoformat(),
                "model_version": self.config['model']['version']
            }
            
            requests.post(
                self.api_config['evidently_capture_url'],
                json=payload,
                timeout=2
            )
            
        except Exception as e:
            # Don't fail if Evidently capture fails
            logger.debug(f"Evidently capture failed: {e}")
    
    def run_simulation(
        self,
        n_requests: int = 100,
        scenario: str = "normal",
        requests_per_second: float = 2.0,
        capture_to_evidently: bool = True,
        show_progress: bool = True
    ) -> Dict:
        """Run simulation with specified parameters"""
        
        logger.info("="*60)
        logger.info(f"{Fore.CYAN}Starting Simulation{Style.RESET_ALL}")
        logger.info("="*60)
        logger.info(f"Scenario: {scenario}")
        logger.info(f"Requests: {n_requests}")
        logger.info(f"Rate: {requests_per_second} req/s")
        logger.info(f"Capture to Evidently: {capture_to_evidently}")
        logger.info("="*60)
        
        # Check API health first
        if not self.check_api_health():
            logger.error("API is not healthy. Aborting simulation.")
            return self.stats
        
        # Calculate delay between requests
        delay = 1.0 / requests_per_second if requests_per_second > 0 else 0
        
        # Generate all samples first
        logger.info("Generating samples...")
        samples = self.data_generator.generate_batch(n_requests, scenario)
        
        # Send requests
        if show_progress:
            iterator = tqdm(
                samples,
                desc=f"{Fore.CYAN}Sending predictions{Style.RESET_ALL}",
                unit="req",
                ncols=100
            )
        else:
            iterator = samples
        
        for features in iterator:
            result = self.send_prediction(features, capture_to_evidently)
            
            if result and result['success'] and show_progress:
                # Update progress bar description
                avg_latency = self.stats['total_latency'] / self.stats['total_requests']
                if hasattr(iterator, 'set_postfix'):
                    iterator.set_postfix({
                        'latency': f"{avg_latency:.3f}s",
                        'pred': f"{result['prediction']:.2f}"
                    })
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        
        # Print summary
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Print simulation summary"""
        logger.info("\n" + "="*60)
        logger.info(f"{Fore.GREEN}Simulation Complete{Style.RESET_ALL}")
        logger.info("="*60)
        
        total = self.stats['total_requests']
        success = self.stats['successful_requests']
        failed = self.stats['failed_requests']
        
        logger.info(f"Total Requests:      {total}")
        logger.info(f"Successful:          {Fore.GREEN}{success}{Style.RESET_ALL}")
        logger.info(f"Failed:              {Fore.RED}{failed}{Style.RESET_ALL}")
        
        if total > 0:
            success_rate = (success / total) * 100
            logger.info(f"Success Rate:        {success_rate:.2f}%")
            
            if success > 0:
                avg_latency = self.stats['total_latency'] / success
                logger.info(f"Average Latency:     {avg_latency:.3f}s")
        
        if self.stats['predictions']:
            predictions = self.stats['predictions']
            logger.info(f"\nPrediction Statistics:")
            logger.info(f"  Mean:              {np.mean(predictions):.3f}")
            logger.info(f"  Std:               {np.std(predictions):.3f}")
            logger.info(f"  Min:               {np.min(predictions):.3f}")
            logger.info(f"  Max:               {np.max(predictions):.3f}")
        
        if self.stats['errors']:
            logger.warning(f"\n{Fore.YELLOW}Errors encountered: {len(self.stats['errors'])}{Style.RESET_ALL}")
            for i, error in enumerate(self.stats['errors'][:5]):  # Show first 5
                logger.warning(f"  {i+1}. {error}")
        
        logger.info("="*60)
    
    def run_traffic_pattern(
        self,
        pattern: str = "steady",
        scenario: str = "normal",
        capture_to_evidently: bool = True
    ) -> Dict:
        """Run simulation with predefined traffic pattern"""
        
        traffic_config = self.config['traffic'].get(pattern)
        
        if not traffic_config:
            logger.error(f"Unknown traffic pattern: {pattern}")
            return self.stats
        
        logger.info(f"Running traffic pattern: {pattern}")
        logger.info(f"Description: {traffic_config['description']}")
        
        if pattern == "gradual":
            # Gradually increase RPS
            start_rps = traffic_config['start_rps']
            end_rps = traffic_config['end_rps']
            duration = traffic_config['duration_seconds']
            
            # Calculate requests at each RPS level
            steps = 10
            step_duration = duration / steps
            
            for i in range(steps):
                # Linear interpolation
                current_rps = start_rps + (end_rps - start_rps) * (i / steps)
                n_requests = int(current_rps * step_duration)
                
                logger.info(f"\nStep {i+1}/{steps}: {current_rps:.1f} req/s for {step_duration:.0f}s")
                
                self.run_simulation(
                    n_requests=n_requests,
                    scenario=scenario,
                    requests_per_second=current_rps,
                    capture_to_evidently=capture_to_evidently,
                    show_progress=True
                )
        else:
            # Simple pattern (burst or steady)
            rps = traffic_config['requests_per_second']
            duration = traffic_config['duration_seconds']
            n_requests = int(rps * duration)
            
            self.run_simulation(
                n_requests=n_requests,
                scenario=scenario,
                requests_per_second=rps,
                capture_to_evidently=capture_to_evidently,
                show_progress=True
            )
        
        return self.stats
    
    def trigger_drift_analysis(self, window_size: int = 100) -> Optional[Dict]:
        """Trigger drift analysis in Evidently"""
        try:
            logger.info(f"\nTriggering drift analysis (window: {window_size})...")
            
            response = requests.post(
                self.api_config['evidently_analyze_url'],
                json={"window_size": window_size, "threshold": 0.1},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                logger.info("Drift Analysis Results:")
                logger.info(f"  Drift Detected:      {result.get('drift_detected', False)}")
                logger.info(f"  Drift Score:         {result.get('drift_score', 0):.3f}")
                logger.info(f"  Drifted Features:    {result.get('drifted_count', 0)}")
                
                if result.get('drifted_features'):
                    logger.info(f"  Features: {', '.join(result['drifted_features'])}")
                
                logger.info(f"  Report: {result.get('report_filename', 'N/A')}")
                
                return result
            else:
                logger.error(f"Analysis failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to trigger analysis: {e}")
            return None
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0.0,
            'predictions': [],
            'errors': []
        }


if __name__ == "__main__":
    # Example usage
    simulator = PredictionSimulator()
    
    # Run normal traffic
    simulator.run_simulation(
        n_requests=50,
        scenario="normal",
        requests_per_second=5,
        capture_to_evidently=True
    )
    
    # Trigger drift analysis
    simulator.trigger_drift_analysis(window_size=50)

