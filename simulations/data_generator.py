"""
============================================
DATA GENERATOR
============================================

Generate realistic wine quality data with configurable drift
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import yaml
from pathlib import Path


class WineDataGenerator:
    """Generate wine quality prediction data"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize data generator with config"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.features = self.config['features']
        self.feature_names = list(self.features.keys())
        
        # Remove 'quality' as it's the target
        if 'quality' in self.feature_names:
            self.feature_names.remove('quality')
    
    def generate_normal_sample(self) -> Dict[str, float]:
        """Generate a single normal sample"""
        sample = {}
        
        for feature in self.feature_names:
            params = self.features[feature]
            
            # Generate value from normal distribution
            value = np.random.normal(params['mean'], params['std'])
            
            # Clip to min/max range
            value = np.clip(value, params['min'], params['max'])
            
            sample[feature] = float(value)
        
        return sample
    
    def generate_drifted_sample(
        self,
        drift_multiplier: float = 1.5,
        affected_features: Optional[List[str]] = None,
        noise_level: float = 0.2
    ) -> Dict[str, float]:
        """Generate a drifted sample"""
        sample = self.generate_normal_sample()
        
        # Determine which features to drift
        if affected_features is None:
            # Randomly select features to drift
            n_drift = np.random.randint(2, len(self.feature_names) // 2)
            affected_features = np.random.choice(
                self.feature_names,
                size=n_drift,
                replace=False
            ).tolist()
        
        # Apply drift to selected features
        for feature in affected_features:
            if feature in sample:
                params = self.features[feature]
                
                # Shift mean
                new_mean = params['mean'] * drift_multiplier
                
                # Add noise
                noise = np.random.normal(0, params['std'] * noise_level)
                
                # Generate drifted value
                value = new_mean + noise
                
                # Clip to valid range
                value = np.clip(value, params['min'], params['max'])
                
                sample[feature] = float(value)
        
        return sample
    
    def generate_batch(
        self,
        n_samples: int = 100,
        scenario: str = "normal"
    ) -> List[Dict[str, float]]:
        """Generate batch of samples"""
        
        scenario_config = self.config['scenarios'].get(
            scenario,
            self.config['scenarios']['normal']
        )
        
        samples = []
        
        for _ in range(n_samples):
            if scenario == "normal":
                sample = self.generate_normal_sample()
            else:
                drift_mult = scenario_config.get('drift_multiplier', 1.5)
                noise = scenario_config.get('noise_level', 0.2)
                n_affected = scenario_config.get('affected_features', 3)
                
                # Select random features to drift
                affected = np.random.choice(
                    self.feature_names,
                    size=min(n_affected, len(self.feature_names)),
                    replace=False
                ).tolist()
                
                sample = self.generate_drifted_sample(
                    drift_multiplier=drift_mult,
                    affected_features=affected,
                    noise_level=noise
                )
            
            samples.append(sample)
        
        return samples
    
    def generate_dataframe(
        self,
        n_samples: int = 100,
        scenario: str = "normal"
    ) -> pd.DataFrame:
        """Generate DataFrame of samples"""
        samples = self.generate_batch(n_samples, scenario)
        return pd.DataFrame(samples)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names.copy()


if __name__ == "__main__":
    # Test data generator
    print("Testing Data Generator...")
    
    gen = WineDataGenerator()
    
    print(f"\nFeatures: {gen.get_feature_names()}")
    
    # Generate normal sample
    print("\nNormal Sample:")
    sample = gen.generate_normal_sample()
    for k, v in sample.items():
        print(f"  {k}: {v:.3f}")
    
    # Generate drifted sample
    print("\nDrifted Sample (severe):")
    drifted = gen.generate_drifted_sample(drift_multiplier=2.0)
    for k, v in drifted.items():
        print(f"  {k}: {v:.3f}")
    
    # Generate batch
    print("\nGenerating batch...")
    df = gen.generate_dataframe(n_samples=10, scenario="moderate_drift")
    print(df.describe())

