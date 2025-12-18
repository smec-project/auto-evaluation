#!/usr/bin/env python3
"""
App Server Executor

This module manages various application servers on edge_server host:
- File Transfer Server
- File Transfer SMEC Server
- File Transfer Tutti Server
- Video Transcoding Server
- Video Transcoding SMEC Server
- Video Transcoding Tutti Server
- Video Detection Server
- Video Detection SMEC Server
- Video Detection Tutti Server
- Video SR Server
- Video SR SMEC Server
- Video SR Tutti Server
"""

import logging
from typing import Dict, Any, Optional
from .host_manager import HostManager
from .config_loader import ConfigLoader


class AppServerExecutor:
    """Executor for managing application servers on edge_server."""

    def __init__(
        self,
        config_file: str = "hosts_config.yaml",
        config_loader: Optional[ConfigLoader] = None,
    ):
        """
        Initialize the app server executor.

        Args:
            config_file: Path to the host configuration file
            config_loader: Optional ConfigLoader instance for dynamic parameter support
        """
        self.host_manager = HostManager(config_file)
        self.config_loader = config_loader
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def _get_app_path(self, scheduler: str, app_folder: str) -> str:
        """
        Get application path based on scheduler type and app folder.

        Args:
            scheduler: Scheduler type (default, smec, tutti, arma)
            app_folder: Application folder name (file-transfer, video-od, video-sr, video-transcoding)

        Returns:
            Full path to the application server directory
        """
        # Get apps_path from config
        edge_server_config = self.host_manager.config.get("hosts", {}).get(
            "edge_server", {}
        )
        apps_path = edge_server_config.get("paths", {}).get(
            "apps_path", "~/edge-applications"
        )

        return f"{apps_path}/{scheduler}/{app_folder}/server"

    def _get_dynamic_param(self) -> str:
        """
        Get the dynamic parameter string if dynamic mode is enabled.

        Returns:
            " -d" if dynamic is enabled, empty string otherwise
        """
        if self.config_loader and self.config_loader.is_dynamic_enabled():
            return " -d"
        return ""

    def _generate_cpu_affinity(self, num_cpus: int) -> str:
        """
        Generate CPU affinity string for taskset using the first n odd-numbered CPUs.

        Args:
            num_cpus: Number of CPUs to use

        Returns:
            CPU list string for taskset (e.g., "1,3,5,7")
        """
        # Generate the first num_cpus odd-numbered CPUs (1, 3, 5, 7, ...)
        odd_cpus = [str(1 + 2 * i) for i in range(num_cpus)]
        return ",".join(odd_cpus)

    def _add_cpu_affinity(self, command: str, num_cpus: int) -> str:
        """
        Add CPU affinity (taskset) to a command for non-SMEC applications.
        Uses bash -c to ensure taskset applies to the entire command sequence.

        Args:
            command: Original command
            num_cpus: Number of CPUs to use

        Returns:
            Command with taskset CPU affinity
        """
        cpu_list = self._generate_cpu_affinity(num_cpus)
        return f'taskset -c {cpu_list} bash -i -c "{command}"'

    # File Transfer Server Functions
    def start_file_transfer_server(self, num_cpus: int = 32) -> Dict[str, Any]:
        """
        Start file transfer server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer server on edge_server...")

        app_path = self._get_app_path("default", "file-transfer")
        base_command = f"cd {app_path} && python3 main.py"
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="file_server",
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
                "connection_info": "edge_server",
            }

    def stop_file_transfer_server(self) -> Dict[str, Any]:
        """
        Stop file transfer server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_server 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer SMEC Server Functions
    def start_file_transfer_smec_server(self) -> Dict[str, Any]:
        """
        Start file transfer SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer SMEC server on edge_server...")

        app_path = self._get_app_path("smec", "file-transfer")
        command = f"cd {app_path} && python3 main.py"

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="file_server_smec",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer SMEC server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer SMEC server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer SMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_file_transfer_smec_server(self) -> Dict[str, Any]:
        """
        Stop file transfer SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer SMEC server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_server_smec 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer SMEC server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer SMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer Tutti Server Functions
    def start_file_transfer_tutti_server(
        self, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start file transfer Tutti server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting file transfer Tutti server on edge_server..."
        )

        app_path = self._get_app_path("tutti", "file-transfer")
        base_command = f"cd {app_path} && python3 main.py"
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="file_server_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer Tutti server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer Tutti server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer Tutti server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_file_transfer_tutti_server(self) -> Dict[str, Any]:
        """
        Stop file transfer Tutti server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping file transfer Tutti server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t file_server_tutti 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer Tutti server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer Tutti server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer ARMA Server Functions
    def start_file_transfer_arma_server(
        self, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start file transfer ARMA server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting file transfer ARMA server on edge_server...")

        app_path = self._get_app_path("arma", "file-transfer")
        base_command = f"cd {app_path} && python3 main.py"
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="file_server_arma",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer ARMA server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer ARMA server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer ARMA server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_file_transfer_arma_server(self) -> Dict[str, Any]:
        """
        Stop file transfer ARMA server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer ARMA server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_server_arma 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer ARMA server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer ARMA server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Server Functions
    def start_video_transcoding_server(
        self, instance_count: int = 2, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video transcoding server on edge_server.

        Args:
            instance_count: Number of server instances to start
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding server on edge_server with"
            f" {instance_count} instances..."
        )

        app_path = self._get_app_path("default", "video-transcoding")
        dynamic_param = self._get_dynamic_param()
        base_command = (
            f"cd {app_path} && make"
            " clean && make -j 8 && python3 run.py"
            f" {instance_count}{dynamic_param} && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
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
                "connection_info": "edge_server",
            }

    def stop_video_transcoding_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding 2>/dev/null || true; "
                "sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video transcoding server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding SMEC Server Functions
    def start_video_transcoding_smec_server(
        self, instance_count: int = 2
    ) -> Dict[str, Any]:
        """
        Start video transcoding SMEC server on edge_server.

        Args:
            instance_count: Number of server instances to start

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding SMEC server on edge_server with"
            f" {instance_count} instances..."
        )

        dynamic_param = self._get_dynamic_param()
        app_path = self._get_app_path("smec", "video-transcoding")
        ignore_drop_param = (
            self.config_loader.get_smec_ignore_drop()
            if self.config_loader
            else 0
        )
        command = (
            f"cd {app_path} &&"
            " make clean && make -j 8 && python3 run.py"
            f" {instance_count} --ignore-drop"
            f" {ignore_drop_param}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_transcoding_smec",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding SMEC server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding SMEC server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding SMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_transcoding_smec_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video transcoding SMEC server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_smec 2>/dev/null ||"
                " true; sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding SMEC server stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding SMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Tutti Server Functions
    def start_video_transcoding_tutti_server(
        self, instance_count: int = 2, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video transcoding Tutti server on edge_server.

        Args:
            instance_count: Number of server instances to start
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding Tutti server on edge_server with"
            f" {instance_count} instances..."
        )

        app_path = self._get_app_path("tutti", "video-transcoding")
        dynamic_param = self._get_dynamic_param()
        base_command = (
            f"cd {app_path} &&"
            " make clean && make -j 8 && python3 run.py"
            f" {instance_count}{dynamic_param} && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_transcoding_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding Tutti server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding Tutti server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding Tutti server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_transcoding_tutti_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding Tutti server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video transcoding Tutti server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_tutti 2>/dev/null ||"
                " true; sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding Tutti server stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding Tutti server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding ARMA Server Functions
    def start_video_transcoding_arma_server(
        self, instance_count: int = 2, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video transcoding ARMA server on edge_server.

        Args:
            instance_count: Number of server instances to start
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding ARMA server on edge_server with"
            f" {instance_count} instances..."
        )

        app_path = self._get_app_path("arma", "video-transcoding")
        dynamic_param = self._get_dynamic_param()
        base_command = (
            f"cd {app_path} &&"
            " make clean && make -j 8 && python3 run.py"
            f" {instance_count}{dynamic_param} && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_transcoding_arma",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding ARMA server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding ARMA server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding ARMA server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_transcoding_arma_server(self) -> Dict[str, Any]:
        """
        Stop video transcoding ARMA server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video transcoding ARMA server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_arma 2>/dev/null ||"
                " true; sudo pkill -f 'transcoder' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding ARMA server stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding ARMA server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection Server Functions
    def start_video_detection_server(
        self, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video detection server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video detection server on edge_server...")

        app_path = self._get_app_path("default", "video-od")
        yolo_model = (
            self.config_loader.get_yolo_model()
            if self.config_loader
            else "yolov8m.pt"
        )
        base_command = (
            f"cd {app_path} &&"
            " make clean && make -j 8 &&"
            " source ~/miniconda3/etc/profile.d/conda.sh && conda activate"
            f" video-detection && ./multi_video_detection {yolo_model} 2 10 &&"
            " tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_detection",
            )

            if result["success"]:
                self.logger.info("Video detection server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video detection server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_detection_server(self) -> Dict[str, Any]:
        """
        Stop video detection server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video detection server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection 2>/dev/null || true; "
                "sudo pkill -f 'multi_video_detection' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video detection server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection SMEC Server Functions
    def start_video_detection_smec_server(self) -> Dict[str, Any]:
        """
        Start video detection SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection SMEC server on edge_server..."
        )

        app_path = self._get_app_path("smec", "video-od")
        ignore_drop_param = (
            self.config_loader.get_smec_ignore_drop()
            if self.config_loader
            else 0
        )
        yolo_model = (
            self.config_loader.get_yolo_model()
            if self.config_loader
            else "yolov8m.pt"
        )
        command = (
            f"cd {app_path}"
            " && export CONDA_PREFIX=~/miniconda3 && export"
            " PATH=/usr/local/cuda/bin:~/miniconda3/bin:$PATH && make clean &&"
            " make -j 8 && source ~/miniconda3/etc/profile.d/conda.sh && conda"
            " activate video-detection && ./multi_video_detection"
            f" {yolo_model} 2 {ignore_drop_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_detection_smec",
            )

            if result["success"]:
                self.logger.info(
                    "Video detection SMEC server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video detection SMEC server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection SMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_detection_smec_server(self) -> Dict[str, Any]:
        """
        Stop video detection SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video detection SMEC server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection_smec 2>/dev/null || true;"
                " sudo pkill -f 'multi_video_detection' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video detection SMEC server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection SMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection Tutti Server Functions
    def start_video_detection_tutti_server(
        self, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video detection Tutti server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection Tutti server on edge_server..."
        )

        app_path = self._get_app_path("tutti", "video-od")
        yolo_model = (
            self.config_loader.get_yolo_model()
            if self.config_loader
            else "yolov8m.pt"
        )
        base_command = (
            f"cd {app_path}"
            " && make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate"
            f" video-detection && ./multi_video_detection {yolo_model} 2 10 &&"
            " tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_detection_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "Video detection Tutti server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video detection Tutti server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection Tutti server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_detection_tutti_server(self) -> Dict[str, Any]:
        """
        Stop video detection Tutti server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video detection Tutti server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection_tutti 2>/dev/null ||"
                " true; sudo pkill -f 'multi_video_detection' 2>/dev/null ||"
                " true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video detection Tutti server stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection Tutti server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection ARMA Server Functions
    def start_video_detection_arma_server(
        self, num_cpus: int = 32
    ) -> Dict[str, Any]:
        """
        Start video detection ARMA server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection ARMA server on edge_server..."
        )

        app_path = self._get_app_path("arma", "video-od")
        yolo_model = (
            self.config_loader.get_yolo_model()
            if self.config_loader
            else "yolov8m.pt"
        )
        base_command = (
            f"cd {app_path}"
            " && make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate"
            f" video-detection && ./multi_video_detection {yolo_model} 2 10 &&"
            " tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_detection_arma",
            )

            if result["success"]:
                self.logger.info(
                    "Video detection ARMA server started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video detection ARMA server:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection ARMA server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_detection_arma_server(self) -> Dict[str, Any]:
        """
        Stop video detection ARMA server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Stopping video detection ARMA server on edge_server..."
        )

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection_arma 2>/dev/null ||"
                " true; sudo pkill -f 'multi_video_detection' 2>/dev/null ||"
                " true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video detection ARMA server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection ARMA server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video SR Server Functions
    def start_video_sr_server(self, num_cpus: int = 32) -> Dict[str, Any]:
        """
        Start video SR server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video SR server on edge_server...")

        app_path = self._get_app_path("default", "video-sr")
        base_command = (
            f"cd {app_path} && "
            "make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate video-sr &&"
            " ./multi_video_sr 2 10 && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_sr",
            )

            if result["success"]:
                self.logger.info("Video SR server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during video SR server startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_sr_server(self) -> Dict[str, Any]:
        """
        Stop video SR server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr 2>/dev/null || true; "
                "sudo pkill -f 'multi_video_sr' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(f"Exception during video SR server cleanup: {e}")
            return {"success": False, "error": str(e)}

    # Video SR SMEC Server Functions
    def start_video_sr_smec_server(self) -> Dict[str, Any]:
        """
        Start video SR SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video SR SMEC server on edge_server...")

        app_path = self._get_app_path("smec", "video-sr")
        ignore_drop_param = (
            self.config_loader.get_smec_ignore_drop()
            if self.config_loader
            else 0
        )
        command = (
            f"cd {app_path} && "
            "make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate video-sr &&"
            f" ./multi_video_sr 2 {ignore_drop_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_sr_smec",
            )

            if result["success"]:
                self.logger.info("Video SR SMEC server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR SMEC server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR SMEC server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_sr_smec_server(self) -> Dict[str, Any]:
        """
        Stop video SR SMEC server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR SMEC server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr_smec 2>/dev/null || true; "
                "sudo pkill -f 'multi_video_sr' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR SMEC server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR SMEC server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video SR Tutti Server Functions
    def start_video_sr_tutti_server(self, num_cpus: int = 32) -> Dict[str, Any]:
        """
        Start video SR Tutti server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video SR Tutti server on edge_server...")

        app_path = self._get_app_path("tutti", "video-sr")
        base_command = (
            f"cd {app_path} && "
            "make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate video-sr &&"
            " ./multi_video_sr 2 10 && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_sr_tutti",
            )

            if result["success"]:
                self.logger.info("Video SR Tutti server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR Tutti server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR Tutti server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_sr_tutti_server(self) -> Dict[str, Any]:
        """
        Stop video SR Tutti server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR Tutti server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr_tutti 2>/dev/null || true; "
                "sudo pkill -f 'multi_video_sr' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR Tutti server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR Tutti server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video SR ARMA Server Functions
    def start_video_sr_arma_server(self, num_cpus: int = 32) -> Dict[str, Any]:
        """
        Start video SR ARMA server on edge_server.

        Args:
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting video SR ARMA server on edge_server...")

        app_path = self._get_app_path("arma", "video-sr")
        base_command = (
            f"cd {app_path} && "
            "make clean && make -j 8 && source"
            " ~/miniconda3/etc/profile.d/conda.sh && conda activate video-sr &&"
            " ./multi_video_sr 2 10 && tail -f /dev/null"
        )
        command = self._add_cpu_affinity(base_command, num_cpus)

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge_server",
                command=command,
                session_name="video_sr_arma",
            )

            if result["success"]:
                self.logger.info("Video SR ARMA server started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR ARMA server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR ARMA server startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge_server",
            }

    def stop_video_sr_arma_server(self) -> Dict[str, Any]:
        """
        Stop video SR ARMA server on edge_server.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR ARMA server on edge_server...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr_arma 2>/dev/null || true; "
                "sudo pkill -f 'multi_video_sr' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge_server", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR ARMA server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR ARMA server cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_all_servers(
        self,
        video_transcoding_instance_count: int = 2,
        num_cpus: int = 32,
    ) -> Dict[str, Any]:
        """
        Start all application servers.

        Args:
            video_transcoding_instance_count: Number of instances for video transcoding servers
            num_cpus: Number of CPUs to use for CPU affinity (default: 32)

        Returns:
            Dictionary containing results for all servers
        """
        self.logger.info("Starting all application servers...")

        results = {
            "file_server": self.start_file_transfer_server(num_cpus),
            "file_server_smec": self.start_file_transfer_smec_server(),
            "file_server_tutti": self.start_file_transfer_tutti_server(
                num_cpus
            ),
            "file_server_arma": self.start_file_transfer_arma_server(num_cpus),
            "video_transcoding": self.start_video_transcoding_server(
                video_transcoding_instance_count, num_cpus
            ),
            "video_transcoding_smec": self.start_video_transcoding_smec_server(
                video_transcoding_instance_count
            ),
            "video_transcoding_tutti": self.start_video_transcoding_tutti_server(
                video_transcoding_instance_count, num_cpus
            ),
            "video_transcoding_arma": self.start_video_transcoding_arma_server(
                video_transcoding_instance_count, num_cpus
            ),
            "video_detection": self.start_video_detection_server(num_cpus),
            "video_detection_smec": self.start_video_detection_smec_server(),
            "video_detection_tutti": self.start_video_detection_tutti_server(
                num_cpus
            ),
            "video_detection_arma": self.start_video_detection_arma_server(
                num_cpus
            ),
            "video_sr": self.start_video_sr_server(num_cpus),
            "video_sr_smec": self.start_video_sr_smec_server(),
            "video_sr_tutti": self.start_video_sr_tutti_server(num_cpus),
            "video_sr_arma": self.start_video_sr_arma_server(num_cpus),
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
            "file_server_smec": self.stop_file_transfer_smec_server(),
            "file_server_tutti": self.stop_file_transfer_tutti_server(),
            "file_server_arma": self.stop_file_transfer_arma_server(),
            "video_transcoding": self.stop_video_transcoding_server(),
            "video_transcoding_smec": self.stop_video_transcoding_smec_server(),
            "video_transcoding_tutti": self.stop_video_transcoding_tutti_server(),
            "video_transcoding_arma": self.stop_video_transcoding_arma_server(),
            "video_detection": self.stop_video_detection_server(),
            "video_detection_smec": self.stop_video_detection_smec_server(),
            "video_detection_tutti": self.stop_video_detection_tutti_server(),
            "video_detection_arma": self.stop_video_detection_arma_server(),
            "video_sr": self.stop_video_sr_server(),
            "video_sr_smec": self.stop_video_sr_smec_server(),
            "video_sr_tutti": self.stop_video_sr_tutti_server(),
            "video_sr_arma": self.stop_video_sr_arma_server(),
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
                host_name="edge_server",
                command=(
                    "tmux list-sessions 2>/dev/null || echo 'No tmux sessions'"
                ),
                background=False,
            )

            status = {
                "file_server": False,
                "file_server_smec": False,
                "file_server_tutti": False,
                "file_server_arma": False,
                "video_transcoding": False,
                "video_transcoding_smec": False,
                "video_transcoding_tutti": False,
                "video_transcoding_arma": False,
                "video_detection": False,
                "video_detection_smec": False,
                "video_detection_tutti": False,
                "video_detection_arma": False,
                "video_sr": False,
                "video_sr_smec": False,
                "video_sr_tutti": False,
                "video_sr_arma": False,
                "tmux_output": result.get("output", ""),
            }

            if result["success"] and result.get("output"):
                output = result["output"]
                status["file_server"] = "file_server:" in output
                status["file_server_smec"] = "file_server_smec:" in output
                status["file_server_tutti"] = "file_server_tutti:" in output
                status["file_server_arma"] = "file_server_arma:" in output
                status["video_transcoding"] = "video_transcoding:" in output
                status["video_transcoding_smec"] = (
                    "video_transcoding_smec:" in output
                )
                status["video_transcoding_tutti"] = (
                    "video_transcoding_tutti:" in output
                )
                status["video_transcoding_arma"] = (
                    "video_transcoding_arma:" in output
                )
                status["video_detection"] = "video_detection:" in output
                status["video_detection_smec"] = (
                    "video_detection_smec:" in output
                )
                status["video_detection_tutti"] = (
                    "video_detection_tutti:" in output
                )
                status["video_detection_arma"] = (
                    "video_detection_arma:" in output
                )
                status["video_sr"] = "video_sr:" in output
                status["video_sr_smec"] = "video_sr_smec:" in output
                status["video_sr_tutti"] = "video_sr_tutti:" in output
                status["video_sr_arma"] = "video_sr_arma:" in output

            return status

        except Exception as e:
            self.logger.error(f"Exception during status check: {e}")
            return {
                "file_server": False,
                "file_server_smec": False,
                "file_server_tutti": False,
                "file_server_arma": False,
                "video_transcoding": False,
                "video_transcoding_smec": False,
                "video_transcoding_tutti": False,
                "video_transcoding_arma": False,
                "video_detection": False,
                "video_detection_smec": False,
                "video_detection_tutti": False,
                "video_detection_arma": False,
                "video_sr": False,
                "video_sr_smec": False,
                "video_sr_tutti": False,
                "video_sr_arma": False,
                "error": str(e),
            }
