#!/usr/bin/env python3
"""
Baseline Transcoding Experiment

This script manages the baseline transcoding experiment:
- 0: Start experiment (basic env setup -> app servers -> app clients)
- 1: End experiment (cleanup apps -> cleanup basic env)

Usage:
    python baseline_transcoding.py 0  # Start experiment
    python baseline_transcoding.py 1  # End experiment
"""

import sys
import logging
import time
from src.basic_env_setup import BasicEnvSetup
from src.app_server_executor import AppServerExecutor
from src.app_client_executor import AppClientExecutor


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def test_connections():
    """Test connections to required hosts."""
    logger = logging.getLogger(__name__)
    logger.info("=== Testing Host Connections ===")

    # Use BasicEnvSetup to test connections
    basic_setup = BasicEnvSetup()
    connection_status = basic_setup.host_manager.test_connections()

    for host, status in connection_status.items():
        status_symbol = "✓" if status else "✗"
        logger.info(f"  {host}: {status_symbol}")

    # Check if required hosts are available
    required_hosts = ["amari", "edge0", "edge1"]
    missing_hosts = [
        host
        for host in required_hosts
        if not connection_status.get(host, False)
    ]

    if missing_hosts:
        logger.error(
            f"Error: Missing connections to required hosts: {missing_hosts}"
        )
        return False

    logger.info("All required hosts are accessible")
    return True


def start_experiment():
    """Start the baseline transcoding experiment."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("STARTING BASELINE TRANSCODING EXPERIMENT")
    logger.info("=" * 60)

    # Test connections first
    if not test_connections():
        logger.error("Connection test failed, aborting experiment")
        return False

    # Step 1: Setup basic environment (LTE + 5G)
    logger.info("\n=== STEP 1: Basic Environment Setup ===")
    basic_setup = BasicEnvSetup()

    logger.info("Starting basic environment setup (LTE + 5G)...")
    basic_results = basic_setup.setup_complete_environment(wait_time=3)

    if not basic_results.get("overall_success", False):
        logger.error("Basic environment setup failed, aborting experiment")
        logger.error(
            "LTE restart success:"
            f" {basic_results.get('lte_restart', {}).get('success', False)}"
        )
        logger.error(
            "5G gNB start success:"
            f" {basic_results.get('5g_gnb_start', {}).get('success', False)}"
        )
        return False

    logger.info("✓ Basic environment setup completed successfully")
    logger.info(f"  - LTE service restarted on amari")
    logger.info(
        "  - 5G gNB started on edge0 (PID:"
        f" {basic_results.get('5g_gnb_start', {}).get('pid', 'N/A')})"
    )
    logger.info("Waiting 10 seconds before starting next step...")
    time.sleep(10)

    # Step 2: Start application servers on edge1
    logger.info("\n=== STEP 2: Application Servers Setup ===")
    app_server = AppServerExecutor()

    logger.info("Starting file transfer server...")
    file_server_result = app_server.start_file_transfer_server()
    if not file_server_result["success"]:
        logger.error("Failed to start file transfer server")
        return False
    logger.info("✓ File transfer server started successfully")

    # Wait between server starts
    logger.info("Waiting 3 seconds before starting next server...")
    time.sleep(3)

    logger.info("Starting video transcoding server...")
    video_server_result = app_server.start_video_transcoding_server()
    if not video_server_result["success"]:
        logger.error("Failed to start video transcoding server")
        return False
    logger.info("✓ Video transcoding server started successfully")

    # Wait for servers to initialize
    logger.info("Waiting 10 seconds for servers to initialize...")
    time.sleep(10)

    # Step 3: Start application clients on amari
    logger.info("\n=== STEP 3: Application Clients Setup ===")
    app_client = AppClientExecutor()

    logger.info("Starting video transcoding client...")
    video_client_result = app_client.start_video_transcoding_client()
    if not video_client_result["success"]:
        logger.error("Failed to start video transcoding client")
        return False
    logger.info("✓ Video transcoding client started successfully")

    # Wait between client starts
    logger.info("Waiting 3 seconds before starting next client...")
    time.sleep(2)

    logger.info("Starting file transfer client...")
    file_client_result = app_client.start_file_transfer_client()
    if not file_client_result["success"]:
        logger.error("Failed to start file transfer client")
        return False
    logger.info("✓ File transfer client started successfully")

    # Wait between client starts
    logger.info("Waiting 3 seconds before summing up...")
    time.sleep(3)

    # Final status check
    logger.info("\n=== EXPERIMENT STATUS ===")
    logger.info("✓ Basic environment (LTE + 5G) is running")
    logger.info("✓ Application servers are running on edge1:")
    logger.info("  - File transfer server (tmux: file_server)")
    logger.info("  - Video transcoding server (tmux: video_transcoding)")
    logger.info("✓ Application clients are running on amari:")
    logger.info("  - File transfer client (tmux: file_transfer)")
    logger.info("  - Video transcoding client (tmux: video_transcoding)")

    logger.info("\n" + "=" * 60)
    logger.info("BASELINE TRANSCODING EXPERIMENT STARTED SUCCESSFULLY")
    logger.info("=" * 60)

    return True


def end_experiment():
    """End the baseline transcoding experiment."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("ENDING BASELINE TRANSCODING EXPERIMENT")
    logger.info("=" * 60)

    # Test connections first
    if not test_connections():
        logger.error("Connection test failed, proceeding with cleanup anyway")

    success = True

    # Step 1: Cleanup application clients
    logger.info("\n=== STEP 1: Application Clients Cleanup ===")
    app_client = AppClientExecutor()

    logger.info("Stopping file transfer client...")
    file_client_result = app_client.stop_file_transfer_client()
    if file_client_result["success"]:
        logger.info("✓ File transfer client stopped")
    else:
        logger.warning("⚠ File transfer client cleanup had issues")
        success = False

    logger.info("Stopping video transcoding client...")
    video_client_result = app_client.stop_video_transcoding_client()
    if video_client_result["success"]:
        logger.info("✓ Video transcoding client stopped")
    else:
        logger.warning("⚠ Video transcoding client cleanup had issues")
        success = False

    # Step 2: Cleanup application servers
    logger.info("\n=== STEP 2: Application Servers Cleanup ===")
    app_server = AppServerExecutor()

    logger.info("Stopping file transfer server...")
    file_server_result = app_server.stop_file_transfer_server()
    if file_server_result["success"]:
        logger.info("✓ File transfer server stopped")
    else:
        logger.warning("⚠ File transfer server cleanup had issues")
        success = False

    logger.info("Stopping video transcoding server...")
    video_server_result = app_server.stop_video_transcoding_server()
    if video_server_result["success"]:
        logger.info("✓ Video transcoding server stopped")
    else:
        logger.warning("⚠ Video transcoding server cleanup had issues")
        success = False

    # Step 3: Cleanup basic environment
    logger.info("\n=== STEP 3: Basic Environment Cleanup ===")
    basic_setup = BasicEnvSetup()

    logger.info("Cleaning up basic environment (LTE + 5G)...")
    cleanup_results = basic_setup.cleanup_environment()

    if cleanup_results.get("overall_success", False):
        logger.info("✓ Basic environment cleanup completed")
        logger.info("  - LTE service stopped on amari")
        logger.info("  - 5G gNB stopped on edge0")
    else:
        logger.warning("⚠ Basic environment cleanup had issues")
        logger.warning(
            "  LTE stop success:"
            f" {cleanup_results.get('lte_stop', {}).get('success', False)}"
        )
        logger.warning(
            "  5G gNB stop success:"
            f" {cleanup_results.get('5g_gnb_stop', {}).get('success', False)}"
        )
        success = False

    # Final status
    logger.info("\n=== CLEANUP STATUS ===")
    if success:
        logger.info("✓ All components cleaned up successfully")
        logger.info("✓ Application clients stopped on amari")
        logger.info("✓ Application servers stopped on edge1")
        logger.info("✓ Basic environment (LTE + 5G) cleaned up")

        logger.info("\n" + "=" * 60)
        logger.info("BASELINE TRANSCODING EXPERIMENT ENDED SUCCESSFULLY")
        logger.info("=" * 60)
    else:
        logger.warning("⚠ Experiment cleanup completed with some issues")
        logger.warning("Please check the logs above for details")

        logger.info("\n" + "=" * 60)
        logger.info("BASELINE TRANSCODING EXPERIMENT ENDED WITH WARNINGS")
        logger.info("=" * 60)

    return success


def print_usage():
    """Print usage information."""
    print("Baseline Transcoding Experiment")
    print("=" * 40)
    print("Usage:")
    print("  python baseline_transcoding.py 0  # Start experiment")
    print("  python baseline_transcoding.py 1  # End experiment")
    print("")
    print("Experiment Flow:")
    print("  Start (0):")
    print("    1. Setup basic environment (LTE + 5G)")
    print(
        "    2. Start app servers on edge1 (file transfer + video transcoding)"
    )
    print(
        "    3. Start app clients on amari (file transfer + video transcoding)"
    )
    print("")
    print("  End (1):")
    print("    1. Stop app clients on amari")
    print("    2. Stop app servers on edge1")
    print("    3. Cleanup basic environment (LTE + 5G)")


def main():
    """Main function."""
    # Setup logging
    logger = setup_logging()

    # Check command line arguments
    if len(sys.argv) != 2:
        logger.error("Invalid number of arguments")
        print_usage()
        sys.exit(1)

    try:
        action = int(sys.argv[1])
    except ValueError:
        logger.error("Invalid argument: must be 0 or 1")
        print_usage()
        sys.exit(1)

    if action not in [0, 1]:
        logger.error("Invalid action: must be 0 (start) or 1 (end)")
        print_usage()
        sys.exit(1)

    # Execute the requested action
    start_time = time.time()

    if action == 0:
        logger.info("Starting baseline transcoding experiment...")
        success = start_experiment()
        action_name = "start experiment"
    else:
        logger.info("Ending baseline transcoding experiment...")
        success = end_experiment()
        action_name = "end experiment"

    end_time = time.time()
    duration = end_time - start_time

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info(f"Action: {action_name}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
    logger.info("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
