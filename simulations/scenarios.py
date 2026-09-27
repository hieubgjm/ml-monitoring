#!/usr/bin/env python3
"""
============================================
PRE-CONFIGURED SCENARIOS
============================================

Ready-to-use simulation scenarios
"""

import time
from simulator import PredictionSimulator
from colorama import Fore, Style, init
import logging

init(autoreset=True)
logger = logging.getLogger(__name__)


def scenario_1_normal_day():
    """Simulate a normal day of traffic"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 1: Normal Day Traffic")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Simulating 8 hours of steady normal traffic...")
    
    simulator = PredictionSimulator()
    
    # 8 hours of normal traffic at 1 req/sec
    simulator.run_simulation(
        n_requests=8 * 3600,  # 8 hours worth
        scenario="normal",
        requests_per_second=5,  # Simulate faster (5 req/s)
        capture_to_evidently=True
    )
    
    simulator.trigger_drift_analysis(window_size=500)


def scenario_2_gradual_drift():
    """Simulate gradual drift introduction"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 2: Gradual Drift Introduction")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Simulating drift gradually appearing over time...")
    
    simulator = PredictionSimulator()
    
    # Phase 1: Normal traffic
    print(f"\n{Fore.GREEN}Phase 1: Normal Operation (100 requests){Style.RESET_ALL}")
    simulator.run_simulation(
        n_requests=100,
        scenario="normal",
        requests_per_second=5,
        capture_to_evidently=True
    )
    
    time.sleep(2)
    
    # Phase 2: Slight drift starts
    print(f"\n{Fore.YELLOW}Phase 2: Slight Drift Appears (100 requests){Style.RESET_ALL}")
    simulator.run_simulation(
        n_requests=100,
        scenario="slight_drift",
        requests_per_second=5,
        capture_to_evidently=True
    )
    
    time.sleep(2)
    
    # Phase 3: Drift becomes moderate
    print(f"\n{Fore.YELLOW}Phase 3: Drift Intensifies (100 requests){Style.RESET_ALL}")
    simulator.run_simulation(
        n_requests=100,
        scenario="moderate_drift",
        requests_per_second=5,
        capture_to_evidently=True
    )
    
    # Analyze
    simulator.trigger_drift_analysis(window_size=200)


def scenario_3_sudden_shift():
    """Simulate sudden data distribution shift"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 3: Sudden Distribution Shift")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Simulating sudden change in data distribution...")
    
    simulator = PredictionSimulator()
    
    # Before shift
    print(f"\n{Fore.GREEN}Before Shift: Normal Traffic (200 requests){Style.RESET_ALL}")
    simulator.run_simulation(
        n_requests=200,
        scenario="normal",
        requests_per_second=10,
        capture_to_evidently=True
    )
    
    time.sleep(5)
    
    # After shift
    print(f"\n{Fore.RED}After Shift: Severe Drift (200 requests){Style.RESET_ALL}")
    simulator.run_simulation(
        n_requests=200,
        scenario="sudden_shift",
        requests_per_second=10,
        capture_to_evidently=True
    )
    
    # Analyze
    simulator.trigger_drift_analysis(window_size=300)


def scenario_4_traffic_spike():
    """Simulate traffic spike with normal data"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 4: Traffic Spike")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Simulating sudden increase in traffic...")
    
    simulator = PredictionSimulator()
    
    # Use burst traffic pattern
    simulator.run_traffic_pattern(
        pattern="burst",
        scenario="normal",
        capture_to_evidently=True
    )


def scenario_5_mixed_conditions():
    """Simulate mixed normal and drift conditions"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 5: Mixed Conditions")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Simulating alternating normal and drift periods...")
    
    simulator = PredictionSimulator()
    
    scenarios = ["normal", "moderate_drift", "normal", "severe_drift", "normal"]
    
    for i, scenario in enumerate(scenarios, 1):
        color = Fore.GREEN if "normal" in scenario else Fore.YELLOW
        print(f"\n{color}Period {i}/{len(scenarios)}: {scenario}{Style.RESET_ALL}")
        
        simulator.run_simulation(
            n_requests=50,
            scenario=scenario,
            requests_per_second=5,
            capture_to_evidently=True
        )
        
        time.sleep(2)
    
    # Analyze
    simulator.trigger_drift_analysis(window_size=200)


def scenario_6_stress_test():
    """Stress test with high traffic"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("SCENARIO 6: Stress Test")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("Running high-volume traffic test...")
    
    simulator = PredictionSimulator()
    
    # High RPS for extended period
    simulator.run_simulation(
        n_requests=1000,
        scenario="normal",
        requests_per_second=20,
        capture_to_evidently=True
    )
    
    simulator.trigger_drift_analysis(window_size=500)


def run_all_scenarios():
    """Run all scenarios sequentially"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print("RUNNING ALL SCENARIOS")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    scenarios = [
        ("Normal Day", scenario_1_normal_day),
        ("Gradual Drift", scenario_2_gradual_drift),
        ("Sudden Shift", scenario_3_sudden_shift),
        ("Traffic Spike", scenario_4_traffic_spike),
        ("Mixed Conditions", scenario_5_mixed_conditions),
        ("Stress Test", scenario_6_stress_test),
    ]
    
    for i, (name, func) in enumerate(scenarios, 1):
        print(f"\n{Fore.CYAN}Running Scenario {i}/{len(scenarios)}: {name}{Style.RESET_ALL}")
        
        try:
            func()
            print(f"{Fore.GREEN}✓ Scenario {i} completed{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Scenario {i} failed: {e}{Style.RESET_ALL}")
        
        # Wait between scenarios
        if i < len(scenarios):
            print(f"\n{Fore.YELLOW}Waiting 10 seconds before next scenario...{Style.RESET_ALL}")
            time.sleep(10)
    
    print(f"\n{Fore.GREEN}{'='*60}")
    print("ALL SCENARIOS COMPLETED")
    print(f"{'='*60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run pre-configured simulation scenarios")
    parser.add_argument(
        'scenario',
        type=int,
        nargs='?',
        choices=[1, 2, 3, 4, 5, 6],
        help='Scenario number to run (1-6), or omit to run all'
    )
    
    args = parser.parse_args()
    
    scenarios_map = {
        1: ("Normal Day", scenario_1_normal_day),
        2: ("Gradual Drift", scenario_2_gradual_drift),
        3: ("Sudden Shift", scenario_3_sudden_shift),
        4: ("Traffic Spike", scenario_4_traffic_spike),
        5: ("Mixed Conditions", scenario_5_mixed_conditions),
        6: ("Stress Test", scenario_6_stress_test),
    }
    
    if args.scenario:
        name, func = scenarios_map[args.scenario]
        print(f"\nRunning Scenario {args.scenario}: {name}")
        func()
    else:
        run_all_scenarios()

