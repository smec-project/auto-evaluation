#!/usr/bin/env python3
"""
PMEC Transcoding Experiment

This script manages the PMEC transcoding experiment:
- 0: Start experiment (PMEC env setup -> PMEC app servers -> PMEC app clients)
- 1: End experiment (cleanup PMEC apps -> cleanup PMEC env)

Usage:
    python pmec_transcoding.py 0  # Start experiment
    python pmec_transcoding.py 1  # End experiment
"""

import sys
import logging
import time
from src.pmec_env_setup import PMECEnvSetup
from src.app_server_executor import AppServerExecutor
from src.app_client_executor import AppClientExecutor
from src.pmec_controller import PMECController
from src.amari_ping_test import AmariPingTest


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

    # Use PMECEnvSetup to test connections
    pmec_setup = PMECEnvSetup()
    connection_status = pmec_setup.host_manager.test_connections()

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
    """Start the PMEC transcoding experiment."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("STARTING PMEC TRANSCODING EXPERIMENT")
    logger.info("=" * 60)

    # Test connections first
    if not test_connections():
        logger.error("Connection test failed, aborting experiment")
        return False

    # Step 1: Setup PMEC environment (LTE + 5G + PMEC Controller)
    logger.info("\n=== STEP 1: PMEC Environment Setup ===")
    pmec_setup = PMECEnvSetup()

    logger.info(
        "Starting PMEC environment setup (LTE + 5G + PMEC Controller)..."
    )
    pmec_results = pmec_setup.setup_complete_environment(wait_time=3)

    if not pmec_results.get("overall_success", False):
        logger.error("PMEC environment setup failed, aborting experiment")
        logger.error(
            "LTE restart success:"
            f" {pmec_results.get('lte_restart', {}).get('success', False)}"
        )
        logger.error(
            "5G gNB start success:"
            f" {pmec_results.get('5g_gnb_start', {}).get('success', False)}"
        )
        logger.error(
            "PMEC controller start success:"
            f" {pmec_results.get('pmec_controller_start', {}).get('success', False)}"
        )
        return False

    logger.info("✓ PMEC environment setup completed successfully")
    logger.info(f"  - LTE service restarted on amari")
    logger.info(
        "  - 5G gNB started on edge0 (PID:"
        f" {pmec_results.get('5g_gnb_start', {}).get('pid', 'N/A')})"
    )
    logger.info(f"  - PMEC controller started on edge0")

    # Wait 15 seconds before starting next phase
    logger.info("Waiting 15 seconds before starting PMEC servers...")
    time.sleep(15)

    # Network connectivity check
    logger.info("\n=== NETWORK CONNECTIVITY CHECK ===")
    ping_test = AmariPingTest()
    if not ping_test.quick_health_check():
        logger.error("Network connectivity check failed, aborting experiment")
        return False
    logger.info("✓ Network connectivity verified")

    # Step 2: Start PMEC controller system (edge1 + amari)
    logger.info("\n=== STEP 2: PMEC Controller System Setup ===")
    pmec_controller = PMECController()

    logger.info("Starting PMEC controller system...")
    controller_results = pmec_controller.start_pmec_system()

    if not controller_results.get("overall_success", False):
        logger.error("PMEC controller system setup failed")
        logger.error(
            "PMEC server success:"
            f" {controller_results.get('server', {}).get('success', False)}"
        )
        logger.error(
            "PMEC client success:"
            f" {controller_results.get('client', {}).get('success', False)}"
        )
        return False

    logger.info("✓ PMEC controller system started successfully")
    logger.info(f"  - PMEC server started on edge1")
    logger.info(f"  - PMEC client started on amari")

    # Wait 3 seconds before starting app servers
    logger.info("Waiting 10 seconds before starting application servers...")
    time.sleep(10)

    # Step 3: Start PMEC application servers on edge1
    logger.info("\n=== STEP 3: PMEC Application Servers Setup ===")
    app_server = AppServerExecutor()

    # logger.info("Starting file transfer PMEC server...")
    file_server_result = app_server.start_file_transfer_pmec_server()
    if not file_server_result["success"]:
        logger.error("Failed to start file transfer PMEC server")
        return False
    logger.info("✓ File transfer PMEC server started successfully")

    # Wait between server starts
    logger.info("Waiting 3 seconds before starting next server...")
    time.sleep(3)

    logger.info("Starting video transcoding PMEC server...")
    video_server_result = app_server.start_video_transcoding_pmec_server()
    if not video_server_result["success"]:
        logger.error("Failed to start video transcoding PMEC server")
        return False
    logger.info("✓ Video transcoding PMEC server started successfully")

    # Wait for servers to initialize
    logger.info("Waiting 10 seconds for servers to initialize...")
    time.sleep(10)

    # Step 4: Start PMEC application clients on amari
    logger.info("\n=== STEP 4: PMEC Application Clients Setup ===")
    app_client = AppClientExecutor()

    logger.info("Starting video transcoding PMEC client...")
    video_client_result = app_client.start_video_transcoding_pmec_client()
    if not video_client_result["success"]:
        logger.error("Failed to start video transcoding PMEC client")
        return False
    logger.info("✓ Video transcoding PMEC client started successfully")

    # Wait between client starts
    logger.info("Waiting 3 seconds before starting next client...")
    time.sleep(2)

    logger.info("Starting file transfer PMEC client...")
    file_client_result = app_client.start_file_transfer_pmec_client()
    if not file_client_result["success"]:
        logger.error("Failed to start file transfer PMEC client")
        return False
    logger.info("✓ File transfer PMEC client started successfully")

    # Wait between client starts
    logger.info("Waiting 3 seconds before summing up...")
    time.sleep(3)

    # Final status check
    logger.info("\n=== EXPERIMENT STATUS ===")
    logger.info("✓ PMEC environment (LTE + 5G + PMEC Controller) is running")
    logger.info("✓ PMEC controller system is running:")
    logger.info("  - PMEC server on edge1 (tmux: pmec_controller)")
    logger.info("  - PMEC client on amari (tmux: pmec_controller)")
    logger.info("✓ PMEC application servers are running on edge1:")
    logger.info("  - File transfer PMEC server (tmux: file_server_pmec)")
    logger.info(
        "  - Video transcoding PMEC server (tmux: video_transcoding_pmec)"
    )
    logger.info("✓ PMEC application clients are running on amari:")
    logger.info("  - File transfer PMEC client (tmux: file_transfer_pmec)")
    logger.info(
        "  - Video transcoding PMEC client (tmux: video_transcoding_pmec)"
    )

    logger.info("\n" + "=" * 60)
    logger.info("PMEC TRANSCODING EXPERIMENT STARTED SUCCESSFULLY")
    logger.info("=" * 60)

    return True


def end_experiment():
    """End the PMEC transcoding experiment."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("ENDING PMEC TRANSCODING EXPERIMENT")
    logger.info("=" * 60)

    # Test connections first
    if not test_connections():
        logger.error("Connection test failed, proceeding with cleanup anyway")

    success = True

    # Step 1: Cleanup PMEC application clients
    logger.info("\n=== STEP 1: PMEC Application Clients Cleanup ===")
    app_client = AppClientExecutor()

    logger.info("Stopping file transfer PMEC client...")
    file_client_result = app_client.stop_file_transfer_pmec_client()
    if file_client_result["success"]:
        logger.info("✓ File transfer PMEC client stopped")
    else:
        logger.warning("⚠ File transfer PMEC client cleanup had issues")
        success = False

    logger.info("Stopping video transcoding PMEC client...")
    video_client_result = app_client.stop_video_transcoding_pmec_client()
    if video_client_result["success"]:
        logger.info("✓ Video transcoding PMEC client stopped")
    else:
        logger.warning("⚠ Video transcoding PMEC client cleanup had issues")
        success = False

    # Step 2: Cleanup PMEC application servers
    logger.info("\n=== STEP 2: PMEC Application Servers Cleanup ===")
    app_server = AppServerExecutor()

    logger.info("Stopping file transfer PMEC server...")
    file_server_result = app_server.stop_file_transfer_pmec_server()
    if file_server_result["success"]:
        logger.info("✓ File transfer PMEC server stopped")
    else:
        logger.warning("⚠ File transfer PMEC server cleanup had issues")
        success = False

    logger.info("Stopping video transcoding PMEC server...")
    video_server_result = app_server.stop_video_transcoding_pmec_server()
    if video_server_result["success"]:
        logger.info("✓ Video transcoding PMEC server stopped")
    else:
        logger.warning("⚠ Video transcoding PMEC server cleanup had issues")
        success = False

    # Step 3: Cleanup PMEC controller system
    logger.info("\n=== STEP 3: PMEC Controller System Cleanup ===")
    pmec_controller = PMECController()

    logger.info("Stopping PMEC controller system...")
    controller_results = pmec_controller.stop_pmec_system()

    if controller_results.get("overall_success", False):
        logger.info("✓ PMEC controller system stopped")
        logger.info("  - PMEC server stopped on edge1")
        logger.info("  - PMEC client stopped on amari")
    else:
        logger.warning("⚠ PMEC controller system cleanup had issues")
        logger.warning(
            "  PMEC server stop success:"
            f" {controller_results.get('server', {}).get('success', False)}"
        )
        logger.warning(
            "  PMEC client stop success:"
            f" {controller_results.get('client', {}).get('success', False)}"
        )
        success = False

    # Step 4: Cleanup PMEC environment
    logger.info("\n=== STEP 4: PMEC Environment Cleanup ===")
    pmec_setup = PMECEnvSetup()

    logger.info("Cleaning up PMEC environment (LTE + 5G + PMEC Controller)...")
    cleanup_results = pmec_setup.cleanup_environment()

    if cleanup_results.get("overall_success", False):
        logger.info("✓ PMEC environment cleanup completed")
        logger.info("  - LTE service stopped on amari")
        logger.info("  - 5G gNB stopped on edge0")
        logger.info("  - PMEC controller stopped on edge0")
    else:
        logger.warning("⚠ PMEC environment cleanup had issues")
        logger.warning(
            "  LTE stop success:"
            f" {cleanup_results.get('lte_stop', {}).get('success', False)}"
        )
        logger.warning(
            "  5G gNB stop success:"
            f" {cleanup_results.get('5g_gnb_stop', {}).get('success', False)}"
        )
        logger.warning(
            "  PMEC controller stop success:"
            f" {cleanup_results.get('pmec_controller_stop', {}).get('success', False)}"
        )
        success = False

    # Final status
    logger.info("\n=== CLEANUP STATUS ===")
    if success:
        logger.info("✓ All PMEC components cleaned up successfully")
        logger.info("✓ PMEC application clients stopped on amari")
        logger.info("✓ PMEC application servers stopped on edge1")
        logger.info("✓ PMEC controller system stopped")
        logger.info(
            "✓ PMEC environment (LTE + 5G + PMEC Controller) cleaned up"
        )

        logger.info("\n" + "=" * 60)
        logger.info("PMEC TRANSCODING EXPERIMENT ENDED SUCCESSFULLY")
        logger.info("=" * 60)
    else:
        logger.warning("⚠ PMEC experiment cleanup completed with some issues")
        logger.warning("Please check the logs above for details")

        logger.info("\n" + "=" * 60)
        logger.info("PMEC TRANSCODING EXPERIMENT ENDED WITH WARNINGS")
        logger.info("=" * 60)

    return success


def print_usage():
    """Print usage information."""
    print("PMEC Transcoding Experiment")
    print("=" * 40)
    print("Usage:")
    print("  python pmec_transcoding.py 0  # Start experiment")
    print("  python pmec_transcoding.py 1  # End experiment")
    print("")
    print("Experiment Flow:")
    print("  Start (0):")
    print("    1. Setup PMEC environment (LTE + 5G + PMEC Controller on edge0)")
    print("    2. Start PMEC controller system (edge1 server + amari client)")
    print(
        "    3. Start PMEC app servers on edge1 (file transfer + video"
        " transcoding)"
    )
    print(
        "    4. Start PMEC app clients on amari (file transfer + video"
        " transcoding)"
    )
    print("")
    print("  End (1):")
    print("    1. Stop PMEC app clients on amari")
    print("    2. Stop PMEC app servers on edge1")
    print("    3. Stop PMEC controller system")
    print("    4. Cleanup PMEC environment")


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
        logger.info("Starting PMEC transcoding experiment...")
        success = start_experiment()
        action_name = "start experiment"
    else:
        logger.info("Ending PMEC transcoding experiment...")
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
