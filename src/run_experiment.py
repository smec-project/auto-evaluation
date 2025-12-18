#!/usr/bin/env python3
"""
Experiment Runner Module

This module provides the core function to run SMEC experiments with different operations.
"""

import json
import logging
import sys
from typing import Dict, Any

from src.deployment_operations import (
    deploy_environment,
    cleanup_environment,
    deploy_services_only,
    cleanup_services_only,
)
from src.throughput_test import ThroughputTest


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("experiment.log"),
        ],
    )
    return logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")


def run_experiment(setup_file: str, operation_number: int) -> int:
    """
    Run SMEC experiment with specified configuration and operation.

    Args:
        setup_file: Path to the JSON configuration file
        operation_number: Operation to perform:
                         0 - Full deploy
                         1 - Full cleanup
                         2 - Deploy services only
                         3 - Cleanup services only
                         4 - Throughput test

    Returns:
        Exit code (0 for success, 1 for failure, 2 for throughput warning)
    """
    logger = setup_logging()

    try:
        # Load configuration
        config = load_config(setup_file)
        logger.info(f"Loaded configuration from: {setup_file}")
        logger.info(f"Configuration: {json.dumps(config, indent=2)}")

        if operation_number == 0:
            # Deploy operation
            logger.info("Starting deployment operation...")
            results = deploy_environment(config, setup_file, logger)

            if results["overall_success"]:
                logger.info("Deployment completed successfully!")
                return 0
            else:
                logger.error("Deployment failed!")
                return 1

        elif operation_number == 1:
            # Cleanup operation
            logger.info("Starting cleanup operation...")
            results = cleanup_environment(config, logger)

            if results["overall_success"]:
                logger.info("Cleanup completed successfully!")
                return 0
            else:
                logger.error("Cleanup completed with errors!")
                return 1

        elif operation_number == 2:
            # Deploy services only operation
            logger.info("Starting server and client deployment operation...")
            results = deploy_services_only(config, setup_file, logger)

            if results["overall_success"]:
                logger.info(
                    "Server and client deployment completed successfully!"
                )
                return 0
            else:
                logger.error("Server and client deployment failed!")
                return 1

        elif operation_number == 3:
            # Cleanup services only operation
            logger.info("Starting server and client cleanup operation...")
            results = cleanup_services_only(config, logger)

            if results["overall_success"]:
                logger.info("Server and client cleanup completed successfully!")
                return 0
            else:
                logger.error("Server and client cleanup completed with errors!")
                return 1

        elif operation_number == 4:
            # Throughput test operation
            logger.info("Starting throughput test operation...")

            throughput_tester = ThroughputTest()
            results = throughput_tester.run_throughput_test(
                ue_namespace="ue1",
                duration=10,
                interval=2,
            )

            if results["success"]:
                if results.get("bandwidth_warning", False):
                    logger.warning(
                        "Throughput test completed with bandwidth warning!"
                    )
                    return 2  # Special exit code for warnings
                else:
                    logger.info("Throughput test completed successfully!")
                    return 0
            else:
                logger.error("Throughput test failed!")
                return 1

        else:
            logger.error(
                f"Invalid operation: {operation_number}. Use 0 for deploy, 1"
                " for cleanup, 2 for deploy services only, 3 for cleanup"
                " services only, 4 for throughput test."
            )
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
