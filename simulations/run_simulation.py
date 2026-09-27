#!/usr/bin/env python3
"""
============================================
RUN SIMULATION - CLI Tool
============================================

Command-line interface for running simulations
"""

import argparse
import sys
from pathlib import Path
from colorama import Fore, Style, init

from simulator import PredictionSimulator

init(autoreset=True)


def main():
    parser = argparse.ArgumentParser(
        description="ML Model Prediction Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run normal traffic for 1 minute
  python run_simulation.py --scenario normal --duration 60 --rps 2
  
  # Simulate drift with high traffic
  python run_simulation.py --scenario severe_drift --duration 120 --rps 10
  
  # Run burst traffic pattern
  python run_simulation.py --pattern burst --scenario normal
  
  # Run without capturing to Evidently
  python run_simulation.py --no-capture --requests 100
        """
    )
    
    # Basic options
    parser.add_argument(
        '-n', '--requests',
        type=int,
        default=100,
        help='Number of requests to send (default: 100)'
    )
    
    parser.add_argument(
        '-d', '--duration',
        type=int,
        help='Duration in seconds (overrides --requests if specified)'
    )
    
    parser.add_argument(
        '-r', '--rps',
        type=float,
        default=2.0,
        help='Requests per second (default: 2.0)'
    )
    
    # Scenario selection
    parser.add_argument(
        '-s', '--scenario',
        choices=['normal', 'slight_drift', 'moderate_drift', 'severe_drift', 'sudden_shift'],
        default='normal',
        help='Data scenario to simulate (default: normal)'
    )
    
    # Traffic pattern
    parser.add_argument(
        '-p', '--pattern',
        choices=['burst', 'steady', 'gradual'],
        help='Traffic pattern to use (overrides --requests and --rps)'
    )
    
    # Evidently options
    parser.add_argument(
        '--no-capture',
        action='store_true',
        help='Do not capture data to Evidently'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Trigger drift analysis after completion'
    )
    
    parser.add_argument(
        '--window',
        type=int,
        default=100,
        help='Analysis window size (default: 100)'
    )
    
    # Display options
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (no progress bar)'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Config file path (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate
    if not Path(args.config).exists():
        print(f"{Fore.RED}Error: Config file not found: {args.config}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Initialize simulator
    try:
        simulator = PredictionSimulator(args.config)
    except Exception as e:
        print(f"{Fore.RED}Error initializing simulator: {e}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Run simulation
    try:
        if args.pattern:
            # Use traffic pattern
            simulator.run_traffic_pattern(
                pattern=args.pattern,
                scenario=args.scenario,
                capture_to_evidently=not args.no_capture
            )
        else:
            # Calculate number of requests
            if args.duration:
                n_requests = int(args.rps * args.duration)
            else:
                n_requests = args.requests
            
            # Run simulation
            simulator.run_simulation(
                n_requests=n_requests,
                scenario=args.scenario,
                requests_per_second=args.rps,
                capture_to_evidently=not args.no_capture,
                show_progress=not args.quiet
            )
        
        # Analyze if requested
        if args.analyze:
            simulator.trigger_drift_analysis(window_size=args.window)
        
        # Success
        print(f"\n{Fore.GREEN}✓ Simulation completed successfully{Style.RESET_ALL}")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Simulation interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}Error during simulation: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

