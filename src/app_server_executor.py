#!/usr/bin/env python3
"""
App Server Executor

This module manages various application servers on edge1 host:
- File Transfer Server
- File Transfer PMEC Server
- Video Transcoding Server
- Video Transcoding PMEC Server
"""

import logging
from typing import Dict, Any
from .host_manager import HostManager


class AppServerExecutor:
    """Executor for managing application servers on edge1."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the app server executor.

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

    # File Transfer Server Functions
    def start_file_transfer_server(self) -> Dict[str, Any]:
        """
        Start file transfer server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer server on edge1...")

        command = (
            "cd ~/edge-server-scheduler/edge-apps/file-transfer && "
            "python main.py"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=command, session_name="file_server"
            )

            if result["success"]:
                self.logger.info("File transfer server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start file transfer server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def stop_file_transfer_server(self) -> Dict[str, Any]:
        """
        Stop file transfer server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_server 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer PMEC Server Functions
    def start_file_transfer_pmec_server(self) -> Dict[str, Any]:
        """
        Start file transfer PMEC server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer PMEC server on edge1...")

        command = (
            "cd ~/edge-server-scheduler/edge-apps/file-transfer-pmec && "
            "python main.py"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=command,
                session_name="file_server_pmec",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer PMEC server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer PMEC server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer PMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def stop_file_transfer_pmec_server(self) -> Dict[str, Any]:
        """
        Stop file transfer PMEC server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer PMEC server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_server_pmec 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer PMEC server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer PMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Server Functions
    def start_video_transcoding_server(
        self, instance_count: int = 2
    ) -> Dict[str, Any]:
        """
        Start video transcoding server on edge1.

        Args:
            instance_count: Number of server instances to start

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding server on edge1 with"
            f" {instance_count} instances..."
        )

        command = (
            "cd ~/edge-server-scheduler/edge-apps/video-transcoding && "
            f"taskset -c 0-11 python3 run.py {instance_count}"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=command,
                session_name="video_transcoding",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def stop_video_transcoding_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding 2>/dev/null || true; "
                "sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video transcoding server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding PMEC Server Functions
    def start_video_transcoding_pmec_server(
        self, instance_count: int = 2
    ) -> Dict[str, Any]:
        """
        Start video transcoding PMEC server on edge1.

        Args:
            instance_count: Number of server instances to start

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding PMEC server on edge1 with"
            f" {instance_count} instances..."
        )

        command = (
            "cd ~/edge-server-scheduler/edge-apps/video-transcoding-pmec && "
            f"python3 run.py {instance_count}"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=command,
                session_name="video_transcoding_pmec",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding PMEC server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding PMEC server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding PMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def stop_video_transcoding_pmec_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding PMEC server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding PMEC server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_pmec 2>/dev/null ||"
                " true; sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding PMEC server stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding PMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_all_servers(
        self, video_transcoding_instance_count: int = 2
    ) -> Dict[str, Any]:
        """
        Start all application servers.

        Args:
            video_transcoding_instance_count: Number of instances for video transcoding servers

        Returns:
            Dictionary containing results for all servers
        """
        self.logger.info("Starting all application servers...")

        results = {
            "file_server": self.start_file_transfer_server(),
            "file_server_pmec": self.start_file_transfer_pmec_server(),
            "video_transcoding": self.start_video_transcoding_server(
                video_transcoding_instance_count
            ),
            "video_transcoding_pmec": self.start_video_transcoding_pmec_server(
                video_transcoding_instance_count
            ),
        }

        # Check overall success
        overall_success = all(result["success"] for result in results.values())
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("All application servers started successfully!")
        else:
            self.logger.warning("Some application servers failed to start")

        return results

    def stop_all_servers(self) -> Dict[str, Any]:
        """
        Stop all application servers.

        Returns:
            Dictionary containing results for all servers
        """
        self.logger.info("Stopping all application servers...")

        results = {
            "file_server": self.stop_file_transfer_server(),
            "file_server_pmec": self.stop_file_transfer_pmec_server(),
            "video_transcoding": self.stop_video_transcoding_server(),
            "video_transcoding_pmec": self.stop_video_transcoding_pmec_server(),
        }

        # Check overall success
        overall_success = all(result["success"] for result in results.values())
        results["overall_success"] = overall_success

        if overall_success:
            self.logger.info("All application servers stopped successfully!")
        else:
            self.logger.warning("Some application servers failed to stop")

        return results

    def get_server_status(self) -> Dict[str, Any]:
        """
        Get status of all tmux sessions for application servers.

        Returns:
            Dictionary containing session status information
        """
        self.logger.info("Checking application server status...")

        try:
            # Check all tmux sessions
            result = self.host_manager.execute_on_host(
                host_name="edge1",
                command=(
                    "tmux list-sessions 2>/dev/null || echo 'No tmux sessions'"
                ),
                background=False,
            )

            status = {
                "file_server": False,
                "file_server_pmec": False,
                "video_transcoding": False,
                "video_transcoding_pmec": False,
                "tmux_output": result.get("output", ""),
            }

            if result["success"] and result.get("output"):
                output = result["output"]
                status["file_server"] = "file_server:" in output
                status["file_server_pmec"] = "file_server_pmec:" in output
                status["video_transcoding"] = "video_transcoding:" in output
                status["video_transcoding_pmec"] = (
                    "video_transcoding_pmec:" in output
                )

            return status

        except Exception as e:
            self.logger.error(f"Exception during status check: {e}")
            return {
                "file_server": False,
                "file_server_pmec": False,
                "video_transcoding": False,
                "video_transcoding_pmec": False,
                "error": str(e),
            }
