#!/usr/bin/env python3
"""
Main Entry Point for SMEC Experiment Automation

This script handles the deployment, cleanup, and testing of SMEC experimental environments.
It supports five operations:
- Operation 0: Deploy full environment (basic or SMEC based on configuration)
- Operation 1: Cleanup all deployed services
- Operation 2: Deploy only server and client applications
- Operation 3: Cleanup only server and client applications
- Operation 4: Run throughput test

Usage:
    python main.py <config_file_path> <operation>

    config_file_path: Path to the JSON configuration file
    operation: 0 for full deploy, 1 for full cleanup, 2 for deploy services only,
               3 for cleanup services only, 4 for throughput test
"""

import sys
from src.run_experiment import run_experiment


def main(config_path: str, operation: int) -> int:
    """
    Main function to handle deployment, cleanup, and testing operations.

    Args:
        config_path: Path to the JSON configuration file
        operation: 0 for full deploy, 1 for full cleanup, 2 for deploy services only,
                  3 for cleanup services only, 4 for throughput test

    Returns:
        Exit code (0 for success, 1 for failure, 2 for throughput warning)
    """
    return run_experiment(config_path, operation)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <config_file_path> <operation>")
        print("  config_file_path: Path to JSON configuration file")
        print(
            "  operation: 0 for full deploy, 1 for full cleanup, 2 for deploy"
            " services only,"
        )
        print("             3 for cleanup services only, 4 for throughput test")
        sys.exit(1)

    config_path = sys.argv[1]
    try:
        operation = int(sys.argv[2])
    except ValueError:
        print(
            "Error: operation must be an integer (0 for full deploy, 1 for full"
            " cleanup, 2 for deploy services only, 3 for cleanup services only,"
            " 4 for throughput test)"
        )
        sys.exit(1)

    exit_code = main(config_path, operation)
    sys.exit(exit_code)
