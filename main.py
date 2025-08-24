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

import json
import logging
import sys
import time
from typing import Dict, Any, List

from src.basic_env_setup import BasicEnvSetup
from src.smec_env_setup import SMECEnvSetup
from src.amari_ping_test import AmariPingTest
from src.smec_controller import SMECController
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


def deploy_environment_with_retry(
    config: Dict[str, Any],
    config_path: str,
    logger: logging.Logger,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Deploy the experimental environment with retry logic for ping and iperf tests.

    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary containing deployment results
    """
    logger.info(
        "Starting environment deployment with retry (max retries:"
        f" {max_retries})..."
    )

    num_ues = config.get("num_ues", 8)
    smec_ue_indices = config.get("smec_ue_indices", "")

    for attempt in range(max_retries + 1):
        if attempt > 0:
            logger.info(f"\n=== RETRY ATTEMPT {attempt}/{max_retries} ===")
        else:
            logger.info("\n=== INITIAL DEPLOYMENT ATTEMPT ===")

        # Deploy environment and run tests
        deployment_result = deploy_single_environment_attempt(
            config, config_path, logger, num_ues, smec_ue_indices
        )

        # Check if ping and iperf tests passed
        ping_passed = deployment_result.get("ping_test", {}).get(
            "health_report", {}
        ).get("health_status") in ["EXCELLENT", "GOOD"]
        iperf_passed = deployment_result.get("iperf_test", {}).get(
            "success", False
        )

        if ping_passed and iperf_passed:
            logger.info(
                "✓ Both ping and iperf tests passed, proceeding with"
                " application deployment"
            )
            # Continue with application deployment
            return complete_application_deployment(
                deployment_result, config, config_path, logger, smec_ue_indices
            )
        else:
            # Tests failed, cleanup and retry if attempts remaining
            test_failures = []
            if not ping_passed:
                test_failures.append("ping")
            if not iperf_passed:
                test_failures.append("iperf")

            logger.error(f"✗ Tests failed: {', '.join(test_failures)}")

            if attempt < max_retries:
                logger.info("Cleaning up environment before retry...")
                cleanup_environment(config, logger)
                logger.info("Waiting 10 seconds before next attempt...")
                time.sleep(10)
            else:
                logger.error(
                    f"All {max_retries + 1} deployment attempts failed"
                )
                deployment_result["overall_success"] = False
                return deployment_result

    # This should not be reached
    return {
        "overall_success": False,
        "error": "Deployment failed after all retries",
    }


def deploy_single_environment_attempt(
    config: Dict[str, Any],
    config_path: str,
    logger: logging.Logger,
    num_ues: int,
    smec_ue_indices: str,
) -> Dict[str, Any]:
    """
    Deploy environment and run ping/iperf tests (single attempt).

    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance
        num_ues: Number of UEs
        smec_ue_indices: SMEC UE indices

    Returns:
        Dictionary containing deployment results up to ping/iperf tests
    """
    deployment_results = {
        "env_setup": None,
        "ping_test": None,
        "iperf_test": None,
        "overall_success": False,
    }

    # Step 1: Deploy basic or SMEC environment based on smec_ue_indices
    if smec_ue_indices == "":
        logger.info("Deploying basic environment (smec_ue_indices is empty)")
        env_setup = BasicEnvSetup()
        deployment_results["env_setup"] = env_setup.setup_complete_environment()
    else:
        logger.info(
            f"Deploying SMEC environment (smec_ue_indices: {smec_ue_indices})"
        )
        env_setup = SMECEnvSetup()
        deployment_results["env_setup"] = env_setup.setup_complete_environment()

    if not deployment_results["env_setup"]["overall_success"]:
        logger.error("Environment setup failed, stopping deployment")
        return deployment_results

    # Step 2: Wait 20 seconds and run ping tests
    logger.info("Waiting 20 seconds before running ping tests...")
    time.sleep(20)

    ping_tester = AmariPingTest(num_ues=num_ues)
    deployment_results["ping_test"] = ping_tester.run_all_ping_tests()

    ping_passed = ping_tester.quick_health_check()
    if not ping_passed:
        logger.error("Ping tests failed")
        return deployment_results

    # Step 3: Run iperf test on ue1
    logger.info("Running iperf test on ue1...")
    throughput_tester = ThroughputTest()
    deployment_results["iperf_test"] = throughput_tester.run_throughput_test(
        ue_namespace="ue1", duration=10, interval=2
    )

    if not deployment_results["iperf_test"]["success"]:
        logger.error("Iperf test failed")
        return deployment_results

    logger.info("✓ Both ping and iperf tests passed")
    return deployment_results


def complete_application_deployment(
    deployment_results: Dict[str, Any],
    config: Dict[str, Any],
    config_path: str,
    logger: logging.Logger,
    smec_ue_indices: str,
) -> Dict[str, Any]:
    """
    Complete the application deployment after successful ping/iperf tests.

    Args:
        deployment_results: Results from environment setup and tests
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance
        smec_ue_indices: SMEC UE indices

    Returns:
        Dictionary containing complete deployment results
    """
    # Create ConfigLoader instance for calculating server instances
    experiment_config = ConfigLoader(config_path)

    # Add missing keys to deployment_results
    deployment_results.update(
        {
            "smec_controller": None,
            "server_apps": {},
            "client_apps": {},
        }
    )

    # Step 4: Deploy SMEC controller if smec_ue_indices is not empty
    if smec_ue_indices != "":
        logger.info("Deploying SMEC controller...")
        smec_controller = SMECController()
        num_cpus = experiment_config.get_max_cpus()
        deployment_results["smec_controller"] = (
            smec_controller.start_smec_system(smec_ue_indices, num_cpus)
        )

        if not deployment_results["smec_controller"]["overall_success"]:
            logger.error("SMEC controller deployment failed")
            return deployment_results

        logger.info("Waiting 10 seconds for SMEC controller to stabilize...")
        time.sleep(10)

    # Step 5: Deploy server applications based on config order
    logger.info("Deploying server applications...")
    server_executor = AppServerExecutor()
    num_cpus = experiment_config.get_max_cpus()

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
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_detection_smec"
                    ] = server_executor.start_video_detection_smec_server()
                else:
                    deployment_results["server_apps"]["video_detection"] = (
                        server_executor.start_video_detection_server(num_cpus)
                    )
                server_count += 1

            elif key == "transcoding_ue_indices":
                logger.info("Starting video transcoding server...")
                transcoding_instances = (
                    experiment_config.get_transcoding_server_instances()
                )
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_transcoding_smec"
                    ] = server_executor.start_video_transcoding_smec_server(
                        transcoding_instances
                    )
                else:
                    deployment_results["server_apps"]["video_transcoding"] = (
                        server_executor.start_video_transcoding_server(
                            transcoding_instances, num_cpus
                        )
                    )
                server_count += 1

            elif key == "video_sr_ue_indices":
                logger.info("Starting video SR server...")
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_sr_smec"
                    ] = server_executor.start_video_sr_smec_server()
                else:
                    deployment_results["server_apps"]["video_sr"] = (
                        server_executor.start_video_sr_server(num_cpus)
                    )
                server_count += 1

            elif key == "file_transfer_ue_indices":
                logger.info("Starting file transfer server...")
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "file_transfer_smec"
                    ] = server_executor.start_file_transfer_smec_server()
                else:
                    deployment_results["server_apps"]["file_transfer"] = (
                        server_executor.start_file_transfer_server(num_cpus)
                    )
                server_count += 1

    # Wait for servers to start
    if deployment_results["server_apps"]:
        logger.info("Waiting 15 seconds for server applications to start...")
        time.sleep(15)

    # Step 6: Deploy client applications based on config order
    logger.info("Deploying client applications...")
    client_executor = AppClientExecutor()

    # Deploy clients based on the order they appear in JSON config file
    client_count = 0
    for key in config.keys():
        if key.endswith("_ue_indices") and config[key] != "":
            ue_indices = config[key]

            # Add 2 second delay between client deployments (except for the first one)
            if client_count > 0:
                logger.info("Waiting 8 seconds before starting next client...")
                time.sleep(8)

            if key == "video_detection_ue_indices":
                logger.info(
                    "Starting video detection client with UE indices:"
                    f" {ue_indices}"
                )
                if smec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_detection_smec"
                    ] = client_executor.start_video_detection_smec_client(
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_transcoding_smec"
                    ] = client_executor.start_video_transcoding_smec_client(
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"]["video_sr_smec"] = (
                        client_executor.start_video_sr_smec_client(ue_indices)
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"]["file_transfer_smec"] = (
                        client_executor.start_file_transfer_smec_client(
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
        and deployment_results.get("iperf_test", {}).get(
            "success", True
        )  # Include iperf test result
        and (
            deployment_results["smec_controller"] is None
            or deployment_results["smec_controller"]["overall_success"]
        )
        and server_success
        and client_success
    )

    if deployment_results["overall_success"]:
        logger.info("Environment deployment completed successfully!")
    else:
        logger.error("Environment deployment completed with errors")

    return deployment_results


def deploy_environment(
    config: Dict[str, Any], config_path: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Deploy the experimental environment with retry logic for ping and iperf tests.
    This is a wrapper function that calls deploy_environment_with_retry.

    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance

    Returns:
        Dictionary containing deployment results
    """
    return deploy_environment_with_retry(config, config_path, logger)


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

    smec_ue_indices = config.get("smec_ue_indices", "")

    cleanup_results = {
        "client_apps": {},
        "server_apps": {},
        "smec_controller": None,
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

    # Step 3: Stop SMEC controller if it was deployed
    if smec_ue_indices != "":
        logger.info("Stopping SMEC controller...")
        smec_controller = SMECController()
        cleanup_results["smec_controller"] = smec_controller.stop_smec_system()

    # Step 4: Cleanup environment
    logger.info("Cleaning up environment...")
    if smec_ue_indices != "":
        env_setup = SMECEnvSetup()
        cleanup_results["env_cleanup"] = env_setup.cleanup_environment()
    else:
        env_setup = BasicEnvSetup()
        cleanup_results["env_cleanup"] = env_setup.cleanup_environment()

    # Check overall cleanup success
    cleanup_results["overall_success"] = (
        cleanup_results["client_apps"]["overall_success"]
        and cleanup_results["server_apps"]["overall_success"]
        and (
            cleanup_results["smec_controller"] is None
            or cleanup_results["smec_controller"]["overall_success"]
        )
        and cleanup_results["env_cleanup"]["overall_success"]
    )

    if cleanup_results["overall_success"]:
        logger.info("Environment cleanup completed successfully!")
    else:
        logger.warning("Environment cleanup completed with some errors")

    return cleanup_results


def deploy_services_only(
    config: Dict[str, Any], config_path: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Deploy only server and client applications without environment setup.

    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
        logger: Logger instance

    Returns:
        Dictionary containing deployment results
    """
    logger.info("Starting server and client deployment...")

    experiment_config = ConfigLoader(config_path)
    smec_ue_indices = config.get("smec_ue_indices", "")

    deployment_results = {
        "smec_controller": None,
        "server_apps": {},
        "client_apps": {},
        "overall_success": False,
    }

    # Deploy SMEC controller if smec_ue_indices is not empty
    # if smec_ue_indices != "":
    #     logger.info("Deploying SMEC controller...")
    #     smec_controller = SMECController()
    #     num_cpus = experiment_config.get_max_cpus()
    #     deployment_results["smec_controller"] = (
    #         smec_controller.start_smec_system(smec_ue_indices, num_cpus)
    #     )

    #     if not deployment_results["smec_controller"]["overall_success"]:
    #         logger.error("SMEC controller deployment failed")
    #         return deployment_results

    #     logger.info("Waiting 10 seconds for SMEC controller to stabilize...")
    #     time.sleep(10)

    # Deploy server applications based on config order
    logger.info("Deploying server applications...")
    server_executor = AppServerExecutor()
    num_cpus = experiment_config.get_max_cpus()

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
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_detection_smec"
                    ] = server_executor.start_video_detection_smec_server()
                else:
                    deployment_results["server_apps"]["video_detection"] = (
                        server_executor.start_video_detection_server(num_cpus)
                    )
                server_count += 1

            elif key == "transcoding_ue_indices":
                logger.info("Starting video transcoding server...")
                transcoding_instances = (
                    experiment_config.get_transcoding_server_instances()
                )
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_transcoding_smec"
                    ] = server_executor.start_video_transcoding_smec_server(
                        transcoding_instances
                    )
                else:
                    deployment_results["server_apps"]["video_transcoding"] = (
                        server_executor.start_video_transcoding_server(
                            transcoding_instances, num_cpus
                        )
                    )
                server_count += 1

            elif key == "video_sr_ue_indices":
                logger.info("Starting video SR server...")
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "video_sr_smec"
                    ] = server_executor.start_video_sr_smec_server()
                else:
                    deployment_results["server_apps"]["video_sr"] = (
                        server_executor.start_video_sr_server(num_cpus)
                    )
                server_count += 1

            elif key == "file_transfer_ue_indices":
                logger.info("Starting file transfer server...")
                if smec_ue_indices != "":
                    deployment_results["server_apps"][
                        "file_transfer_smec"
                    ] = server_executor.start_file_transfer_smec_server()
                else:
                    deployment_results["server_apps"]["file_transfer"] = (
                        server_executor.start_file_transfer_server(num_cpus)
                    )
                server_count += 1

    # Wait for servers to start
    if deployment_results["server_apps"]:
        logger.info("Waiting 15 seconds for server applications to start...")
        time.sleep(15)

    # Deploy client applications based on config order
    logger.info("Deploying client applications...")
    client_executor = AppClientExecutor()

    # Deploy clients based on the order they appear in JSON config file
    client_count = 0
    for key in config.keys():
        if key.endswith("_ue_indices") and config[key] != "":
            ue_indices = config[key]

            # Add 2 second delay between client deployments (except for the first one)
            if client_count > 0:
                logger.info("Waiting 8 seconds before starting next client...")
                time.sleep(8)

            if key == "video_detection_ue_indices":
                logger.info(
                    "Starting video detection client with UE indices:"
                    f" {ue_indices}"
                )
                if smec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_detection_smec"
                    ] = client_executor.start_video_detection_smec_client(
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"][
                        "video_transcoding_smec"
                    ] = client_executor.start_video_transcoding_smec_client(
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"]["video_sr_smec"] = (
                        client_executor.start_video_sr_smec_client(ue_indices)
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
                if smec_ue_indices != "":
                    deployment_results["client_apps"]["file_transfer_smec"] = (
                        client_executor.start_file_transfer_smec_client(
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
        (
            deployment_results["smec_controller"] is None
            or deployment_results["smec_controller"]["overall_success"]
        )
        and server_success
        and client_success
    )

    if deployment_results["overall_success"]:
        logger.info("Server and client deployment completed successfully!")
    else:
        logger.error("Server and client deployment completed with errors")

    return deployment_results


def cleanup_services_only(
    config: Dict[str, Any], logger: logging.Logger
) -> Dict[str, Any]:
    """
    Cleanup only server and client applications.

    Args:
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        Dictionary containing cleanup results
    """
    logger.info("Starting server and client cleanup...")

    cleanup_results = {
        "client_apps": {},
        "server_apps": {},
        "smec_controller": None,
        "overall_success": False,
    }

    # Stop client applications
    logger.info("Stopping client applications...")
    client_executor = AppClientExecutor()
    cleanup_results["client_apps"] = client_executor.stop_all_clients()

    # Stop server applications
    logger.info("Stopping server applications...")
    server_executor = AppServerExecutor()
    cleanup_results["server_apps"] = server_executor.stop_all_servers()

    # Stop SMEC controller if it was deployed
    smec_ue_indices = config.get("smec_ue_indices", "")
    if smec_ue_indices != "":
        logger.info("Stopping SMEC controller...")
        smec_controller = SMECController()
        cleanup_results["smec_controller"] = smec_controller.stop_smec_system()

    # Check overall cleanup success
    cleanup_results["overall_success"] = (
        cleanup_results["client_apps"]["overall_success"]
        and cleanup_results["server_apps"]["overall_success"]
        and (
            cleanup_results["smec_controller"] is None
            or cleanup_results["smec_controller"]["overall_success"]
        )
    )

    if cleanup_results["overall_success"]:
        logger.info("Server and client cleanup completed successfully!")
    else:
        logger.warning("Server and client cleanup completed with some errors")

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
    Main function to handle deployment, cleanup, and testing operations.

    Args:
        config_path: Path to the JSON configuration file
        operation: 0 for full deploy, 1 for full cleanup, 2 for deploy services only,
                  3 for cleanup services only, 4 for throughput test

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
            # Deploy services only operation
            logger.info("Starting server and client deployment operation...")
            results = deploy_services_only(config, config_path, logger)

            if results["overall_success"]:
                logger.info(
                    "Server and client deployment completed successfully!"
                )
                return 0
            else:
                logger.error("Server and client deployment failed!")
                return 1

        elif operation == 3:
            # Cleanup services only operation
            logger.info("Starting server and client cleanup operation...")
            results = cleanup_services_only(config, logger)

            if results["overall_success"]:
                logger.info("Server and client cleanup completed successfully!")
                return 0
            else:
                logger.error("Server and client cleanup completed with errors!")
                return 1

        elif operation == 4:
            # Throughput test operation (moved to operation 4)
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
                " cleanup, 2 for deploy services only, 3 for cleanup services"
                " only, 4 for throughput test."
            )
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


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
