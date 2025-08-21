#!/usr/bin/env python3
"""
SMEC Controller

This module manages SMEC (Smart Multi-access Edge Computing) controller components:
- SMEC Controller Server on ipu0 (runs python run.py)
- SMEC Controller Client on amari (runs python run_amarisoft.py 1,2...)
"""

import logging
import time
from typing import Dict, Any
from .host_manager import HostManager


class SMECController:
    """Controller for managing SMEC controller components on ipu0 and amari."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the SMEC controller.

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

    # SMEC Controller Server Functions (ipu0)
    def start_smec_server(self) -> Dict[str, Any]:
        """
        Start SMEC controller server on ipu0.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting SMEC controller server on ipu0...")

        command = "cd ~/edge-server-scheduler && python run.py"

        try:
            result = self.host_manager.execute_on_host(
                host_name="ipu0",
                command=command,
                session_name="smec_controller",
            )

            if result["success"]:
                self.logger.info("SMEC controller server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start SMEC controller server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during SMEC controller server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "ipu0",
            }

    def stop_smec_server(self) -> Dict[str, Any]:
        """
        Stop SMEC controller server on ipu0.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping SMEC controller server on ipu0...")

        try:
            stop_cmd = (
                "tmux kill-session -t smec_controller 2>/dev/null || true; "
                "sudo pkill -f 'server_scheduler' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="ipu0", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("SMEC controller server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during SMEC controller server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # SMEC Controller Client Functions (amari)
    def start_smec_client(self, ue_indices: str = "1,2") -> Dict[str, Any]:
        """
        Start SMEC controller client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting SMEC controller client on amari with UE indices:"
            f" {ue_indices}..."
        )

        command = (
            f"cd ~/edge-client-prober && python run_amarisoft.py {ue_indices}"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="smec_controller",
            )

            if result["success"]:
                self.logger.info("SMEC controller client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start SMEC controller client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during SMEC controller client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_smec_client(self) -> Dict[str, Any]:
        """
        Stop SMEC controller client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping SMEC controller client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t smec_controller 2>/dev/null || true; "
                "sudo pkill -f 'tcp_prober' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("SMEC controller client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during SMEC controller client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_smec_system(self, ue_indices: str = "1,2") -> Dict[str, Any]:
        """
        Start both SMEC controller server and client.

        Note: Server should typically be started before client for proper coordination.

        Args:
            ue_indices: Comma-separated UE indices for the client (e.g., "1,2,3,4")

        Returns:
            Dictionary containing results for both components
        """
        self.logger.info("Starting SMEC controller system...")

        # Start server first, then client
        server_result = self.start_smec_server()
        time.sleep(3)
        client_result = self.start_smec_client(ue_indices)

        results = {
            "server": server_result,
            "client": client_result,
        }

        # Check overall success
        overall_success = server_result["success"] and client_result["success"]
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("SMEC controller system started successfully!")
        else:
            self.logger.warning("SMEC controller system startup had issues")
            if not server_result["success"]:
                self.logger.error("SMEC controller server failed to start")
            if not client_result["success"]:
                self.logger.error("SMEC controller client failed to start")

        return results

    def stop_smec_system(self) -> Dict[str, Any]:
        """
        Stop both SMEC controller server and client.

        Returns:
            Dictionary containing results for both components
        """
        self.logger.info("Stopping SMEC controller system...")

        # Stop both components simultaneously
        server_result = self.stop_smec_server()
        client_result = self.stop_smec_client()

        results = {
            "server": server_result,
            "client": client_result,
        }

        # Check overall success
        overall_success = server_result["success"] and client_result["success"]
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("SMEC controller system stopped successfully!")
        else:
            self.logger.warning("SMEC controller system shutdown had issues")

        return results

    def get_smec_status(self) -> Dict[str, Any]:
        """
        Get status of SMEC controller components on both hosts.

        Returns:
            Dictionary containing status information for both components
        """
        self.logger.info("Checking SMEC controller system status...")

        try:
            # Check server status on ipu0
            server_result = self.host_manager.execute_on_host(
                host_name="ipu0",
                command=(
                    "tmux list-sessions 2>/dev/null | grep smec_controller ||"
                    " echo 'No smec_controller session'"
                ),
                background=False,
            )

            # Check client status on amari
            client_result = self.host_manager.execute_on_host(
                host_name="amari",
                command=(
                    "tmux list-sessions 2>/dev/null | grep smec_controller ||"
                    " echo 'No smec_controller session'"
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
                    "smec_controller:" in server_result["output"]
                )

            if client_result["success"] and client_result.get("output"):
                status["client_running"] = (
                    "smec_controller:" in client_result["output"]
                )

            # Overall system status
            status["system_running"] = (
                status["server_running"] and status["client_running"]
            )

            return status

        except Exception as e:
            self.logger.error(f"Exception during SMEC status check: {e}")
            return {
                "server_running": False,
                "client_running": False,
                "system_running": False,
                "error": str(e),
            }

    def restart_smec_system(self, ue_indices: str = "1,2") -> Dict[str, Any]:
        """
        Restart the entire SMEC controller system.

        This will stop both components and then start them again.

        Args:
            ue_indices: Comma-separated UE indices for the client (e.g., "1,2,3,4")

        Returns:
            Dictionary containing restart operation results
        """
        self.logger.info("Restarting SMEC controller system...")

        # Stop the system first
        stop_results = self.stop_smec_system()

        # Wait a moment for cleanup
        import time

        time.sleep(2)

        # Start the system again
        start_results = self.start_smec_system(ue_indices)

        results = {
            "stop_results": stop_results,
            "start_results": start_results,
            "overall_success": start_results.get("overall_success", False),
        }

        if results["overall_success"]:
            self.logger.info("SMEC controller system restarted successfully!")
        else:
            self.logger.error("SMEC controller system restart failed")

        return results
