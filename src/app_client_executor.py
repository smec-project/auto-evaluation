#!/usr/bin/env python3
"""
App Client Executor

This module manages various application clients on amari host:
- File Transfer Client
- File Transfer PMEC Client
- Video Transcoding Client
- Video Transcoding PMEC Client
"""

import logging
from typing import Dict, Any
from .host_manager import HostManager


class AppClientExecutor:
    """Executor for managing application clients on amari."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the app client executor.

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

    # File Transfer Client Functions
    def start_file_transfer_client(self) -> Dict[str, Any]:
        """
        Start file transfer client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer client on amari...")

        command = (
            "cd ~/edge-client-prober/edge-apps/file-transfer && "
            "python3 run_amarisoft.py 5-8"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari", command=command, session_name="file_transfer"
            )

            if result["success"]:
                self.logger.info("File transfer client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start file transfer client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_file_transfer_client(self) -> Dict[str, Any]:
        """
        Stop file transfer client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_transfer 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer PMEC Client Functions
    def start_file_transfer_pmec_client(self) -> Dict[str, Any]:
        """
        Start file transfer PMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer PMEC client on amari...")

        command = (
            "cd ~/edge-client-prober/edge-apps/file-transfer-pmec && "
            "python3 run_amarisoft.py 5-8"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="file_transfer_pmec",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer PMEC client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer PMEC client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer PMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_file_transfer_pmec_client(self) -> Dict[str, Any]:
        """
        Stop file transfer PMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer PMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_transfer_pmec 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer PMEC client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer PMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Client Functions
    def start_video_transcoding_client(self) -> Dict[str, Any]:
        """
        Start video transcoding client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video transcoding client on amari...")

        command = (
            "cd ~/edge-client-prober/edge-apps/video-transcoding && python3"
            " run_amarisoft.py"
            " ~/video/Inter4K-255-slice16-20M-pingpong-loop8.mp4 2"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_transcoding",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_transcoding_client(self) -> Dict[str, Any]:
        """
        Stop video transcoding client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding 2>/dev/null || true; "
                "sudo pkill -f 'streamer_subscriber' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video transcoding client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding PMEC Client Functions
    def start_video_transcoding_pmec_client(self) -> Dict[str, Any]:
        """
        Start video transcoding PMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video transcoding PMEC client on amari...")

        command = (
            "cd ~/edge-client-prober/edge-apps/video-transcoding-pmec &&"
            " python3 run_amarisoft.py"
            " ~/video/Inter4K-255-slice16-20M-pingpong-loop8.mp4 2"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_transcoding_pmec",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding PMEC client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding PMEC client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding PMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_transcoding_pmec_client(self) -> Dict[str, Any]:
        """
        Stop video transcoding PMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding PMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_pmec 2>/dev/null ||"
                " true; sudo pkill -f 'streamer_subscriber' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding PMEC client stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding PMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_all_clients(self) -> Dict[str, Any]:
        """
        Start all application clients.

        Returns:
            Dictionary containing results for all clients
        """
        self.logger.info("Starting all application clients...")

        results = {
            "file_transfer": self.start_file_transfer_client(),
            "file_transfer_pmec": self.start_file_transfer_pmec_client(),
            "video_transcoding": self.start_video_transcoding_client(),
            "video_transcoding_pmec": self.start_video_transcoding_pmec_client(),
        }

        # Check overall success
        overall_success = all(result["success"] for result in results.values())
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("All application clients started successfully!")
        else:
            self.logger.warning("Some application clients failed to start")

        return results

    def stop_all_clients(self) -> Dict[str, Any]:
        """
        Stop all application clients.

        Returns:
            Dictionary containing results for all clients
        """
        self.logger.info("Stopping all application clients...")

        results = {
            "file_transfer": self.stop_file_transfer_client(),
            "file_transfer_pmec": self.stop_file_transfer_pmec_client(),
            "video_transcoding": self.stop_video_transcoding_client(),
            "video_transcoding_pmec": self.stop_video_transcoding_pmec_client(),
        }

        # Check overall success
        overall_success = all(result["success"] for result in results.values())
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("All application clients stopped successfully!")
        else:
            self.logger.warning("Some application clients failed to stop")

        return results

    def get_client_status(self) -> Dict[str, Any]:
        """
        Get status of all tmux sessions for application clients.

        Returns:
            Dictionary containing session status information
        """
        self.logger.info("Checking application client status...")

        try:
            # Check all tmux sessions
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=(
                    "tmux list-sessions 2>/dev/null || echo 'No tmux sessions'"
                ),
                background=False,
            )

            status = {
                "file_transfer": False,
                "file_transfer_pmec": False,
                "video_transcoding": False,
                "video_transcoding_pmec": False,
                "tmux_output": result.get("output", ""),
            }

            if result["success"] and result.get("output"):
                output = result["output"]
                status["file_transfer"] = "file_transfer:" in output
                status["file_transfer_pmec"] = "file_transfer_pmec:" in output
                status["video_transcoding"] = "video_transcoding:" in output
                status["video_transcoding_pmec"] = (
                    "video_transcoding_pmec:" in output
                )

            return status

        except Exception as e:
            self.logger.error(f"Exception during status check: {e}")
            return {
                "file_transfer": False,
                "file_transfer_pmec": False,
                "video_transcoding": False,
                "video_transcoding_pmec": False,
                "error": str(e),
            }
