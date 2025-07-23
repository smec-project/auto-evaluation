#!/usr/bin/env python3
"""
PMEC Controller

This module manages PMEC (Proximity Multi-access Edge Computing) controller components:
- PMEC Controller Server on edge1 (runs python run.py)
- PMEC Controller Client on amari (runs python run_amarisoft.py 1,2...)
"""

import logging
from typing import Dict, Any
from .host_manager import HostManager


class PMECController:
    """Controller for managing PMEC controller components on edge1 and amari."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the PMEC controller.

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

    # PMEC Controller Server Functions (edge1)
    def start_pmec_server(self) -> Dict[str, Any]:
        """
        Start PMEC controller server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting PMEC controller server on edge1...")

        command = "cd ~/edge-server-scheduler && python run.py"

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=command,
                session_name="pmec_controller",
            )

            if result["success"]:
                self.logger.info("PMEC controller server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start PMEC controller server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during PMEC controller server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def stop_pmec_server(self) -> Dict[str, Any]:
        """
        Stop PMEC controller server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping PMEC controller server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t pmec_controller 2>/dev/null || true; "
                "sudo pkill -f 'server_scheduler' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("PMEC controller server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during PMEC controller server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # PMEC Controller Client Functions (amari)
    def start_pmec_client(self) -> Dict[str, Any]:
        """
        Start PMEC controller client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting PMEC controller client on amari...")

        command = "cd ~/edge-client-prober && python run_amarisoft.py 1,2"

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="pmec_controller",
            )

            if result["success"]:
                self.logger.info("PMEC controller client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start PMEC controller client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during PMEC controller client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_pmec_client(self) -> Dict[str, Any]:
        """
        Stop PMEC controller client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping PMEC controller client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t pmec_controller 2>/dev/null || true; "
                "sudo pkill -f 'tcp_prober' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("PMEC controller client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during PMEC controller client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_pmec_system(self) -> Dict[str, Any]:
        """
        Start both PMEC controller server and client.

        Note: Server should typically be started before client for proper coordination.

        Returns:
            Dictionary containing results for both components
        """
        self.logger.info("Starting PMEC controller system...")

        # Start server first, then client
        server_result = self.start_pmec_server()
        client_result = self.start_pmec_client()

        results = {
            "server": server_result,
            "client": client_result,
        }

        # Check overall success
        overall_success = server_result["success"] and client_result["success"]
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("PMEC controller system started successfully!")
        else:
            self.logger.warning("PMEC controller system startup had issues")
            if not server_result["success"]:
                self.logger.error("PMEC controller server failed to start")
            if not client_result["success"]:
                self.logger.error("PMEC controller client failed to start")

        return results

    def stop_pmec_system(self) -> Dict[str, Any]:
        """
        Stop both PMEC controller server and client.

        Returns:
            Dictionary containing results for both components
        """
        self.logger.info("Stopping PMEC controller system...")

        # Stop both components simultaneously
        server_result = self.stop_pmec_server()
        client_result = self.stop_pmec_client()

        results = {
            "server": server_result,
            "client": client_result,
        }

        # Check overall success
        overall_success = server_result["success"] and client_result["success"]
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("PMEC controller system stopped successfully!")
        else:
            self.logger.warning("PMEC controller system shutdown had issues")

        return results

    def get_pmec_status(self) -> Dict[str, Any]:
        """
        Get status of PMEC controller components on both hosts.

        Returns:
            Dictionary containing status information for both components
        """
        self.logger.info("Checking PMEC controller system status...")

        try:
            # Check server status on edge1
            server_result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=(
                    "tmux list-sessions 2>/dev/null | grep pmec_controller ||"
                    " echo 'No pmec_controller session'"
                ),
                background=False,
            )

            # Check client status on amari
            client_result = self.host_manager.execute_on_host(
                host_name="amari",
                command=(
                    "tmux list-sessions 2>/dev/null | grep pmec_controller ||"
                    " echo 'No pmec_controller session'"
                ),
                background=False,
            )

            status = {
                "server_running": False,
                "client_running": False,
                "server_output": server_result.get("output", ""),
                "client_output": client_result.get("output", ""),
            }

            # Check if sessions are running
            if server_result["success"] and server_result.get("output"):
                status["server_running"] = (
                    "pmec_controller:" in server_result["output"]
                )

            if client_result["success"] and client_result.get("output"):
                status["client_running"] = (
                    "pmec_controller:" in client_result["output"]
                )

            # Overall system status
            status["system_running"] = (
                status["server_running"] and status["client_running"]
            )

            return status

        except Exception as e:
            self.logger.error(f"Exception during PMEC status check: {e}")
            return {
                "server_running": False,
                "client_running": False,
                "system_running": False,
                "error": str(e),
            }

    def restart_pmec_system(self) -> Dict[str, Any]:
        """
        Restart the entire PMEC controller system.

        This will stop both components and then start them again.

        Returns:
            Dictionary containing restart operation results
        """
        self.logger.info("Restarting PMEC controller system...")

        # Stop the system first
        stop_results = self.stop_pmec_system()

        # Wait a moment for cleanup
        import time

        time.sleep(2)

        # Start the system again
        start_results = self.start_pmec_system()

        results = {
            "stop_results": stop_results,
            "start_results": start_results,
            "overall_success": start_results.get("overall_success", False),
        }

        if results["overall_success"]:
            self.logger.info("PMEC controller system restarted successfully!")
        else:
            self.logger.error("PMEC controller system restart failed")

        return results
