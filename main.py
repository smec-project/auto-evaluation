#!/usr/bin/env python3
"""
Main Entry Point for PMEC Experiment Automation

This script handles the deployment, cleanup, and testing of PMEC experimental environments.
It supports three operations:
- Operation 0: Deploy environment (basic or PMEC based on configuration)
- Operation 1: Cleanup all deployed services
- Operation 2: Run throughput test

Usage:
    python main.py <config_file_path> <operation>

    config_file_path: Path to the JSON configuration file
    operation: 0 for deploy, 1 for cleanup, 2 for throughput test
"""

import json
import logging
import sys
import time
from typing import Dict, Any, List

from src.basic_env_setup import BasicEnvSetup
from src.pmec_env_setup import PMECEnvSetup
from src.amari_ping_test import AmariPingTest
from src.pmec_controller import PMECController
from src.app_server_executor import AppServerExecutor
from src.app_client_executor import AppClientExecutor
from src.throughput_test import ThroughputTest
from src.config_loader import ConfigLoader


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


def deploy_environment(
    config: Dict[str, Any], config_path: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Deploy the experimental environment based on configuration.

    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance

    Returns:
        Dictionary containing deployment results
    """
    logger.info("Starting environment deployment...")

    # Create ConfigLoader instance for calculating server instances
    experiment_config = ConfigLoader(config_path)

    num_ues = config.get("num_ues", 8)
    pmec_ue_indices = config.get("pmec_ue_indices", "")

    deployment_results = {
        "env_setup": None,
        "ping_test": None,
        "pmec_controller": None,
        "server_apps": {},
        "client_apps": {},
        "overall_success": False,
    }

    # Step 1: Deploy basic or PMEC environment based on pmec_ue_indices
    if pmec_ue_indices == "":
        logger.info("Deploying basic environment (pmec_ue_indices is empty)")
        env_setup = BasicEnvSetup()
        deployment_results["env_setup"] = env_setup.setup_complete_environment()
    else:
        logger.info(
            f"Deploying PMEC environment (pmec_ue_indices: {pmec_ue_indices})"
        )
        env_setup = PMECEnvSetup()
        deployment_results["env_setup"] = env_setup.setup_complete_environment()

    if not deployment_results["env_setup"]["overall_success"]:
        logger.error("Environment setup failed, stopping deployment")
        return deployment_results

    # Step 2: Wait 15 seconds and run ping tests
    logger.info("Waiting 15 seconds before running ping tests...")
    time.sleep(15)

    ping_tester = AmariPingTest(num_ues=num_ues)
    deployment_results["ping_test"] = ping_tester.run_all_ping_tests()

    if not ping_tester.quick_health_check():
        logger.error("Ping tests failed, stopping deployment")
        return deployment_results

    # Step 3: Deploy PMEC controller if pmec_ue_indices is not empty
    if pmec_ue_indices != "":
        logger.info("Deploying PMEC controller...")
        pmec_controller = PMECController()
        deployment_results["pmec_controller"] = (
            pmec_controller.start_pmec_system(pmec_ue_indices)
        )

        if not deployment_results["pmec_controller"]["overall_success"]:
            logger.error("PMEC controller deployment failed")
            return deployment_results

        logger.info("Waiting 10 seconds for PMEC controller to stabilize...")
        time.sleep(10)

    # Step 4: Deploy server applications based on config order
    logger.info("Deploying server applications...")
    server_executor = AppServerExecutor()

    # Deploy servers based on the order they appear in JSON config file
    server_count = 0
    for key in config.keys():
        if key.endswith("_ue_indices") and config[key] != "":
            # Add 2 second delay between server deployments (except for the first one)
            if server_count > 0:
                logger.info("Waiting 2 seconds before starting next server...")
                time.sleep(2)

            if key == "video_detection_ue_indices":
                logger.info("Starting video detection server...")
                detection_instances = (
                    experiment_config.get_video_detection_server_instances()
                )
                if pmec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_detection_pmec"
                    ] = server_executor.start_video_detection_pmec_server(
                        detection_instances
                    )
                else:
                    deployment_results["server_apps"]["video_detection"] = (
                        server_executor.start_video_detection_server(
                            detection_instances
                        )
                    )
                server_count += 1

            elif key == "transcoding_ue_indices":
                logger.info("Starting video transcoding server...")
                transcoding_instances = (
                    experiment_config.get_transcoding_server_instances()
                )
                if pmec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_transcoding_pmec"
                    ] = server_executor.start_video_transcoding_pmec_server(
                        transcoding_instances
                    )
                else:
                    deployment_results["server_apps"]["video_transcoding"] = (
                        server_executor.start_video_transcoding_server(
                            transcoding_instances
                        )
                    )
                server_count += 1

            elif key == "video_sr_ue_indices":
                logger.info("Starting video SR server...")
                video_sr_instances = (
                    experiment_config.get_video_sr_server_instances()
                )
                if pmec_ue_indices != "":
                    deployment_results["server_apps"]["video_sr_pmec"] = (
                        server_executor.start_video_sr_pmec_server(
                            video_sr_instances
                        )
                    )
                else:
                    deployment_results["server_apps"]["video_sr"] = (
                        server_executor.start_video_sr_server(
                            video_sr_instances
                        )
                    )
                server_count += 1

            elif key == "file_transfer_ue_indices":
                logger.info("Starting file transfer server...")
                if pmec_ue_indices != "":
                    deployment_results["server_apps"][
                        "file_transfer_pmec"
                    ] = server_executor.start_file_transfer_pmec_server()
                else:
                    deployment_results["server_apps"][
                        "file_transfer"
                    ] = server_executor.start_file_transfer_server()
                server_count += 1

    # Wait for servers to start
    if deployment_results["server_apps"]:
        logger.info("Waiting 15 seconds for server applications to start...")
        time.sleep(15)

    # Step 5: Deploy client applications based on config order
    logger.info("Deploying client applications...")
    client_executor = AppClientExecutor()

    # Deploy clients based on the order they appear in JSON config file
    client_count = 0
    for key in config.keys():
        if key.endswith("_ue_indices") and config[key] != "":
            ue_indices = config[key]

            # Add 2 second delay between client deployments (except for the first one)
            if client_count > 0:
                logger.info("Waiting 3 seconds before starting next client...")
                time.sleep(3)

            if key == "video_detection_ue_indices":
                logger.info(
                    "Starting video detection client with UE indices:"
                    f" {ue_indices}"
                )
                if pmec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_detection_pmec"
                    ] = client_executor.start_video_detection_pmec_client(
                        ue_indices
                    )
                else:
                    deployment_results["client_apps"]["video_detection"] = (
                        client_executor.start_video_detection_client(ue_indices)
                    )
                client_count += 1

            elif key == "transcoding_ue_indices":
                logger.info(
                    "Starting video transcoding client with UE indices:"
                    f" {ue_indices}"
                )
                if pmec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_transcoding_pmec"
                    ] = client_executor.start_video_transcoding_pmec_client(
                        ue_indices
                    )
                else:
                    deployment_results["client_apps"]["video_transcoding"] = (
                        client_executor.start_video_transcoding_client(
                            ue_indices
                        )
                    )
                client_count += 1

            elif key == "video_sr_ue_indices":
                logger.info(
                    f"Starting video SR client with UE indices: {ue_indices}"
                )
                if pmec_ue_indices != "":
                    deployment_results["client_apps"]["video_sr_pmec"] = (
                        client_executor.start_video_sr_pmec_client(ue_indices)
                    )
                else:
                    deployment_results["client_apps"]["video_sr"] = (
                        client_executor.start_video_sr_client(ue_indices)
                    )
                client_count += 1

            elif key == "file_transfer_ue_indices":
                logger.info(
                    "Starting file transfer client with UE indices:"
                    f" {ue_indices}"
                )
                if pmec_ue_indices != "":
                    deployment_results["client_apps"]["file_transfer_pmec"] = (
                        client_executor.start_file_transfer_pmec_client(
                            ue_indices
                        )
                    )
                else:
                    deployment_results["client_apps"]["file_transfer"] = (
                        client_executor.start_file_transfer_client(ue_indices)
                    )
                client_count += 1

    # Wait 2 seconds before generating final summary
    logger.info("Waiting 2 seconds before generating deployment summary...")
    time.sleep(2)

    # Check overall deployment success
    server_success = all(
        result.get("success", False)
        for result in deployment_results["server_apps"].values()
    )
    client_success = all(
        result.get("success", False)
        for result in deployment_results["client_apps"].values()
    )

    deployment_results["overall_success"] = (
        deployment_results["env_setup"]["overall_success"]
        and deployment_results["ping_test"]["health_report"]["health_status"]
        in ["EXCELLENT", "GOOD"]
        and (
            deployment_results["pmec_controller"] is None
            or deployment_results["pmec_controller"]["overall_success"]
        )
        and server_success
        and client_success
    )

    if deployment_results["overall_success"]:
        logger.info("Environment deployment completed successfully!")
    else:
        logger.error("Environment deployment completed with errors")

    return deployment_results


def cleanup_environment(
    config: Dict[str, Any], logger: logging.Logger
) -> Dict[str, Any]:
    """
    Cleanup all deployed services.

    Args:
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        Dictionary containing cleanup results
    """
    logger.info("Starting environment cleanup...")

    pmec_ue_indices = config.get("pmec_ue_indices", "")

    cleanup_results = {
        "client_apps": {},
        "server_apps": {},
        "pmec_controller": None,
        "env_cleanup": None,
        "overall_success": False,
    }

    # Step 1: Stop client applications
    logger.info("Stopping client applications...")
    client_executor = AppClientExecutor()
    cleanup_results["client_apps"] = client_executor.stop_all_clients()

    # Step 2: Stop server applications
    logger.info("Stopping server applications...")
    server_executor = AppServerExecutor()
    cleanup_results["server_apps"] = server_executor.stop_all_servers()

    # Step 3: Stop PMEC controller if it was deployed
    if pmec_ue_indices != "":
        logger.info("Stopping PMEC controller...")
        pmec_controller = PMECController()
        cleanup_results["pmec_controller"] = pmec_controller.stop_pmec_system()

    # Step 4: Cleanup environment
    logger.info("Cleaning up environment...")
    if pmec_ue_indices != "":
        env_setup = PMECEnvSetup()
        cleanup_results["env_cleanup"] = env_setup.cleanup_environment()
    else:
        env_setup = BasicEnvSetup()
        cleanup_results["env_cleanup"] = env_setup.cleanup_environment()

    # Check overall cleanup success
    cleanup_results["overall_success"] = (
        cleanup_results["client_apps"]["overall_success"]
        and cleanup_results["server_apps"]["overall_success"]
        and (
            cleanup_results["pmec_controller"] is None
            or cleanup_results["pmec_controller"]["overall_success"]
        )
        and cleanup_results["env_cleanup"]["overall_success"]
    )

    if cleanup_results["overall_success"]:
        logger.info("Environment cleanup completed successfully!")
    else:
        logger.warning("Environment cleanup completed with some errors")

    return cleanup_results


def run_throughput_test(
    config: Dict[str, Any], logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run throughput test on ue1 namespace only.

    Args:
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        Dictionary containing throughput test results
    """
    logger.info("Starting throughput test on ue1...")

    throughput_tester = ThroughputTest()

    # Run throughput test for ue1 only
    test_results = throughput_tester.run_throughput_test(
        ue_namespace="ue1",
        duration=10,  # 10 second test
        interval=2,  # 2 second intervals
    )

    if test_results["success"]:
        if test_results.get("bandwidth_warning", False):
            logger.warning(
                "Throughput test completed with bandwidth warning on ue1!"
            )
        else:
            logger.info("Throughput test completed successfully on ue1!")
    else:
        logger.error("Throughput test failed on ue1!")

    return test_results


def main(config_path: str, operation: int) -> int:
    """
    Main function to handle deployment, cleanup, and throughput test operations.

    Args:
        config_path: Path to the JSON configuration file
        operation: 0 for deploy, 1 for cleanup, 2 for throughput test

    Returns:
        Exit code (0 for success, 1 for failure, 2 for throughput warning)
    """
    logger = setup_logging()

    try:
        # Load configuration
        config = load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
        logger.info(f"Configuration: {json.dumps(config, indent=2)}")

        if operation == 0:
            # Deploy operation
            logger.info("Starting deployment operation...")
            results = deploy_environment(config, config_path, logger)

            if results["overall_success"]:
                logger.info("Deployment completed successfully!")
                return 0
            else:
                logger.error("Deployment failed!")
                return 1

        elif operation == 1:
            # Cleanup operation
            logger.info("Starting cleanup operation...")
            results = cleanup_environment(config, logger)

            if results["overall_success"]:
                logger.info("Cleanup completed successfully!")
                return 0
            else:
                logger.error("Cleanup completed with errors!")
                return 1

        elif operation == 2:
            # Throughput test operation
            logger.info("Starting throughput test operation...")
            results = run_throughput_test(config, logger)

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
                f"Invalid operation: {operation}. Use 0 for deploy, 1 for"
                " cleanup, 2 for throughput test."
            )
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <config_file_path> <operation>")
        print("  config_file_path: Path to JSON configuration file")
        print("  operation: 0 for deploy, 1 for cleanup, 2 for throughput test")
        sys.exit(1)

    config_path = sys.argv[1]
    try:
        operation = int(sys.argv[2])
    except ValueError:
        print(
            "Error: operation must be an integer (0 for deploy, 1 for cleanup,"
            " 2 for throughput test)"
        )
        sys.exit(1)

    exit_code = main(config_path, operation)
    sys.exit(exit_code)
