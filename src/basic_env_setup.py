#!/usr/bin/env python3
"""
Basic Environment Setup Script

This script sets up the basic environment for LTE and 5G testing:
- Restarts LTE service on amari host
- Starts 5G gNB on edge0 host
"""

import logging
import time
from typing import Dict, Any
from .host_manager import HostManager


class BasicEnvSetup:
    """Basic environment setup for LTE and 5G testing."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the basic environment setup.

        Args:
            config_file: Path to the host configuration file
        """
        self.host_manager = HostManager(config_file)
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def restart_lte_service(self) -> Dict[str, Any]:
        """
        Restart LTE service on amari host.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting LTE service restart on amari...")

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command="service lte restart",
                background=False,
            )

            if result["success"]:
                self.logger.info(
                    "LTE service restart command executed successfully"
                )
                self.logger.info(f"Exit code: {result.get('exit_code', 'N/A')}")
                if result.get("output"):
                    self.logger.info(f"Output: {result['output']}")
            else:
                self.logger.error(
                    f"Failed to restart LTE service: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during LTE service restart: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def start_5g_gnb(self) -> Dict[str, Any]:
        """
        Start 5G gNB on edge0 host.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting 5G gNB on edge0...")

        # Command to start 5G gNB with specified configuration files
        gnb_command = (
            "cd ~/srsRAN_Project/build/ && "
            "sudo gnb -c ../configs/gnb_rf_x310_tdd_n78_80mhz-63-samsung.yml "
            "-c ../configs/qam256.yml ../configs/latency-control.yml"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge0", command=gnb_command, session_name="srsran"
            )

            if result["success"]:
                self.logger.info("5G gNB started successfully")
                self.logger.info(f"Process PID: {result['pid']}")
            else:
                self.logger.error(f"Failed to start 5G gNB: {result['error']}")

            return result

        except Exception as e:
            self.logger.error(f"Exception during 5G gNB startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge0",
            }

    def check_lte_service_status(self) -> Dict[str, Any]:
        """
        Check LTE service status on amari host.

        Returns:
            Dictionary containing service status
        """
        self.logger.info("Checking LTE service status on amari...")

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command="service lte status",
                background=False,
            )

            if result["success"]:
                self.logger.info("LTE service status check completed")
                self.logger.info(f"Status output: {result['output']}")
            else:
                self.logger.error(
                    f"Failed to check LTE service status: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during LTE service status check: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def check_5g_gnb_status(self) -> Dict[str, Any]:
        """
        Check 5G gNB process status on edge0 host.

        Returns:
            Dictionary containing gNB status
        """
        self.logger.info("Checking 5G gNB status on edge0...")

        try:
            # Check tmux sessions first, then fallback to process check
            tmux_result = self.host_manager.execute_on_host(
                host_name="edge0",
                command=(
                    "tmux list-sessions 2>/dev/null | grep srsran || echo 'No"
                    " srsran session'"
                ),
                background=False,
            )

            # Also check for gnb processes
            process_result = self.host_manager.execute_on_host(
                host_name="edge0",
                command=(
                    "ps aux | grep 'gnb.*configs' | grep -v grep || echo 'No"
                    " gnb process'"
                ),
                background=False,
            )

            # Combine results
            result = {
                "success": True,
                "output": "",
                "error": "",
                "connection_info": "edge0",
            }

            tmux_info = tmux_result.get("output", "").strip()
            process_info = process_result.get("output", "").strip()

            if "srsran" in tmux_info:
                self.logger.info("5G gNB tmux session is running")
                self.logger.info(f"Tmux session: {tmux_info}")
                result["output"] += f"Tmux: {tmux_info}\n"

            if "gnb" in process_info and "No gnb process" not in process_info:
                self.logger.info("5G gNB process is running")
                self.logger.info(f"Process info: {process_info}")
                result["output"] += f"Process: {process_info}"

            if not result["output"].strip():
                self.logger.warning(
                    "5G gNB is not running (no tmux session or process found)"
                )
                result["output"] = "No gNB found"

            return result

        except Exception as e:
            self.logger.error(f"Exception during 5G gNB status check: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge0",
            }

    def setup_complete_environment(self, wait_time: int = 10) -> Dict[str, Any]:
        """
        Set up the complete environment (LTE + 5G).

        Args:
            wait_time: Time to wait between operations in seconds

        Returns:
            Dictionary containing setup results for all components
        """
        self.logger.info("Starting complete environment setup...")

        results = {
            "lte_restart": None,
            "5g_gnb_start": None,
            "lte_status": None,
            "5g_gnb_status": None,
            "overall_success": False,
        }

        # Step 1: Restart LTE service
        self.logger.info("Step 1: Restarting LTE service on amari")
        results["lte_restart"] = self.restart_lte_service()

        if not results["lte_restart"]["success"]:
            self.logger.error("LTE service restart failed, stopping setup")
            return results

        # Wait for LTE service to stabilize
        self.logger.info(
            f"Waiting {wait_time} seconds for LTE service to stabilize..."
        )
        time.sleep(wait_time)

        # Step 2: Start 5G gNB
        self.logger.info("Step 2: Starting 5G gNB on edge0")
        results["5g_gnb_start"] = self.start_5g_gnb()

        if not results["5g_gnb_start"]["success"]:
            self.logger.error("5G gNB startup failed")
            return results

        # Wait for 5G gNB to initialize
        self.logger.info(
            f"Waiting {wait_time} seconds for 5G gNB to initialize..."
        )
        time.sleep(wait_time)

        # Step 3: Check LTE service status
        self.logger.info("Step 3: Checking LTE service status")
        results["lte_status"] = self.check_lte_service_status()

        # Step 4: Check 5G gNB status
        self.logger.info("Step 4: Checking 5G gNB status")
        results["5g_gnb_status"] = self.check_5g_gnb_status()

        # Determine overall success
        results["overall_success"] = (
            results["lte_restart"]["success"]
            and results["5g_gnb_start"]["success"]
        )

        if results["overall_success"]:
            self.logger.info("Complete environment setup successful!")
        else:
            self.logger.error("Environment setup completed with errors")

        return results

    def cleanup_environment(self) -> Dict[str, Any]:
        """
        Clean up the environment by stopping services.

        Returns:
            Dictionary containing cleanup results
        """
        self.logger.info("Starting environment cleanup...")

        results = {
            "lte_stop": None,
            "5g_gnb_stop": None,
            "overall_success": False,
        }

        # Stop 5G gNB
        self.logger.info("Stopping 5G gNB on edge0...")
        try:
            # Kill tmux sessions and processes
            stop_cmd = (
                "tmux kill-session -t srsran 2>/dev/null || true; "
                "sudo pkill -f 'gnb' 2>/dev/null || true"
            )
            results["5g_gnb_stop"] = self.host_manager.execute_on_host(
                host_name="edge0", command=stop_cmd, background=False
            )
            # Always consider it successful since we use || true
            results["5g_gnb_stop"]["success"] = True
            self.logger.info("5G gNB cleanup completed (tmux session killed)")
        except Exception as e:
            self.logger.error(f"Exception during 5G gNB cleanup: {e}")
            results["5g_gnb_stop"] = {"success": False, "error": str(e)}

        # Stop LTE service
        self.logger.info("Stopping LTE service on amari...")
        try:
            results["lte_stop"] = self.host_manager.execute_on_host(
                host_name="amari", command="service lte stop", background=False
            )
            if results["lte_stop"]["success"]:
                self.logger.info("LTE service stopped successfully")
            else:
                self.logger.warning("Failed to stop LTE service")
        except Exception as e:
            self.logger.error(f"Exception during LTE service cleanup: {e}")
            results["lte_stop"] = {"success": False, "error": str(e)}

        results["overall_success"] = (
            results["5g_gnb_stop"]["success"] and results["lte_stop"]["success"]
        )

        if results["overall_success"]:
            self.logger.info("Environment cleanup completed successfully!")
        else:
            self.logger.warning(
                "Environment cleanup completed with some errors"
            )

        return results
