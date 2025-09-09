#!/usr/bin/env python3
"""
App Client Executor

This module manages various application clients on amari host:
- File Transfer Client
- File Transfer SMEC Client
- File Transfer Tutti Client
- Video Transcoding Client
- Video Transcoding SMEC Client
- Video Transcoding Tutti Client
- Video Detection Client
- Video Detection SMEC Client
- Video Detection Tutti Client
- Video SR Client
- Video SR SMEC Client
- Video SR Tutti Client
"""

import logging
from typing import Dict, Any, Optional
from .host_manager import HostManager
from .config_loader import ConfigLoader


class AppClientExecutor:
    """Executor for managing application clients on amari."""

    def __init__(
        self,
        config_file: str = "hosts_config.yaml",
        config_loader: Optional[ConfigLoader] = None,
    ):
        """
        Initialize the app client executor.

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

    def _get_dynamic_param(self) -> str:
        """
        Get the dynamic parameter string if dynamic mode is enabled.

        Returns:
            " -d" if dynamic is enabled, empty string otherwise
        """
        if self.config_loader and self.config_loader.is_dynamic_enabled():
            return " -d"
        return ""

    # File Transfer Client Functions
    def start_file_transfer_client(
        self, ue_indices: str = "5,6,7,8"
    ) -> Dict[str, Any]:
        """
        Start file transfer client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting file transfer client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/file-transfer && python3"
            f" run_amarisoft.py {ue_indices}{dynamic_param} && tail -f"
            " /dev/null"
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

    # File Transfer SMEC Client Functions
    def start_file_transfer_smec_client(
        self, ue_indices: str = "5,6,7,8"
    ) -> Dict[str, Any]:
        """
        Start file transfer SMEC client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting file transfer SMEC client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/file-transfer-smec && python3"
            f" run_amarisoft.py {ue_indices}{dynamic_param} && tail -f"
            " /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="file_transfer_smec",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer SMEC client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer SMEC client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer SMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_file_transfer_smec_client(self) -> Dict[str, Any]:
        """
        Stop file transfer SMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer SMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_transfer_smec 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer SMEC client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer SMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # File Transfer Tutti Client Functions
    def start_file_transfer_tutti_client(
        self, ue_indices: str = "5,6,7,8"
    ) -> Dict[str, Any]:
        """
        Start file transfer Tutti client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting file transfer Tutti client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/file-transfer && python3"
            f" run_amarisoft.py {ue_indices}{dynamic_param} && tail -f"
            " /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="file_transfer_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "File transfer Tutti client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start file transfer Tutti client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer Tutti client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_file_transfer_tutti_client(self) -> Dict[str, Any]:
        """
        Stop file transfer Tutti client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping file transfer Tutti client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t file_transfer_tutti 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("File transfer Tutti client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during file transfer Tutti client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Client Functions
    def start_video_transcoding_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video transcoding client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding client on amari with UE indices:"
            f" {ue_indices}..."
        )

        command = (
            "cd ~/edge-client-prober/edge-apps/video-transcoding && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py"
            " ~/video/Inter4K-255-slice16-20M-pingpong-6min.mp4"
            f" {ue_indices} && tail -f /dev/null"
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

    # Video Transcoding SMEC Client Functions
    def start_video_transcoding_smec_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video transcoding SMEC client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding SMEC client on amari with UE indices:"
            f" {ue_indices}..."
        )

        rtt_param = ""
        if self.config_loader:
            rtt_value = self.config_loader.get_smec_rtt()
            if rtt_value > 0:
                rtt_param = f" --rtt {rtt_value}"

        command = (
            "cd ~/edge-client-prober/edge-apps/video-transcoding-smec &&"
            " make clean && make -j 8 && python3 run_amarisoft.py"
            " ~/video/Inter4K-255-slice16-20M-pingpong-6min.mp4"
            f" {ue_indices}{rtt_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_transcoding_smec",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding SMEC client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding SMEC client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding SMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_transcoding_smec_client(self) -> Dict[str, Any]:
        """
        Stop video transcoding SMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding SMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_smec 2>/dev/null ||"
                " true; sudo pkill -f 'streamer_subscriber' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding SMEC client stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding SMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Transcoding Tutti Client Functions
    def start_video_transcoding_tutti_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video transcoding Tutti client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video transcoding Tutti client on amari with UE indices:"
            f" {ue_indices}..."
        )

        command = (
            "cd ~/edge-client-prober/edge-apps/video-transcoding-tutti && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py"
            " ~/video/Inter4K-255-slice16-20M-pingpong-6min.mp4"
            f" {ue_indices} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_transcoding_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "Video transcoding Tutti client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video transcoding Tutti client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding Tutti client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_transcoding_tutti_client(self) -> Dict[str, Any]:
        """
        Stop video transcoding Tutti client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video transcoding Tutti client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_transcoding_tutti 2>/dev/null ||"
                " true; sudo pkill -f 'streamer_subscriber' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video transcoding Tutti client stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video transcoding Tutti client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection Client Functions
    def start_video_detection_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video detection client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-detection && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py"
            " ~/video/MOT17-02-slice16-pingpong-loop3-8Mbps-6min.mp4"
            f" {ue_indices}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_detection",
            )

            if result["success"]:
                self.logger.info("Video detection client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video detection client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_detection_client(self) -> Dict[str, Any]:
        """
        Stop video detection client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video detection client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection 2>/dev/null || true; "
                "sudo pkill -f 'video_detection_client' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video detection client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection SMEC Client Functions
    def start_video_detection_smec_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video detection SMEC client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection SMEC client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        rtt_param = ""
        if self.config_loader:
            rtt_value = self.config_loader.get_smec_rtt()
            if rtt_value > 0:
                rtt_param = f" --rtt {rtt_value}"

        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-detection-smec &&"
            " make clean && make -j 8 && python3 run_amarisoft.py"
            " ~/video/MOT17-02-slice16-pingpong-loop3-8Mbps-6min.mp4"
            f" {ue_indices}{rtt_param}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_detection_smec",
            )

            if result["success"]:
                self.logger.info(
                    "Video detection SMEC client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video detection SMEC client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection SMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_detection_smec_client(self) -> Dict[str, Any]:
        """
        Stop video detection SMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video detection SMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection_smec 2>/dev/null || true;"
                " sudo pkill -f 'video_detection_client' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video detection SMEC client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection SMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video Detection Tutti Client Functions
    def start_video_detection_tutti_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video detection Tutti client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video detection Tutti client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-detection-tutti && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py"
            " ~/video/MOT17-02-slice16-pingpong-loop3-8Mbps-6min.mp4"
            f" {ue_indices}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_detection_tutti",
            )

            if result["success"]:
                self.logger.info(
                    "Video detection Tutti client started successfully"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    "Failed to start video detection Tutti client:"
                    f" {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection Tutti client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_detection_tutti_client(self) -> Dict[str, Any]:
        """
        Stop video detection Tutti client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video detection Tutti client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_detection_tutti 2>/dev/null ||"
                " true; sudo pkill -f 'video_detection_client' 2>/dev/null ||"
                " true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info(
                "Video detection Tutti client stopped successfully"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video detection Tutti client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video SR Client Functions
    def start_video_sr_client(self, ue_indices: str = "1,2") -> Dict[str, Any]:
        """
        Start video SR client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video SR client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-sr && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py ~/video/201_320x180_30fps_qp22_6min.mp4"
            f" {ue_indices}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_sr",
            )

            if result["success"]:
                self.logger.info("Video SR client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during video SR client startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_sr_client(self) -> Dict[str, Any]:
        """
        Stop video SR client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr 2>/dev/null || true; "
                "sudo pkill -f 'video_sr_client' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(f"Exception during video SR client cleanup: {e}")
            return {"success": False, "error": str(e)}

    # Video SR SMEC Client Functions
    def start_video_sr_smec_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video SR SMEC client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video SR SMEC client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        rtt_param = ""
        if self.config_loader:
            rtt_value = self.config_loader.get_smec_rtt()
            if rtt_value > 0:
                rtt_param = f" --rtt {rtt_value}"

        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-sr-smec && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py ~/video/201_320x180_30fps_qp22_6min.mp4"
            f" {ue_indices}{rtt_param}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_sr_smec",
            )

            if result["success"]:
                self.logger.info("Video SR SMEC client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR SMEC client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR SMEC client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_sr_smec_client(self) -> Dict[str, Any]:
        """
        Stop video SR SMEC client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR SMEC client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr_smec 2>/dev/null || true; "
                "sudo pkill -f 'video_sr_client' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR SMEC client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR SMEC client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Video SR Tutti Client Functions
    def start_video_sr_tutti_client(
        self, ue_indices: str = "1,2"
    ) -> Dict[str, Any]:
        """
        Start video SR Tutti client on amari.

        Args:
            ue_indices: Comma-separated UE indices (e.g., "1,2,3,4")

        Returns:
            Dictionary containing execution results
        """
        self.logger.info(
            "Starting video SR Tutti client on amari with UE indices:"
            f" {ue_indices}..."
        )

        dynamic_param = self._get_dynamic_param()
        command = (
            "cd ~/edge-client-prober/edge-apps/multi-video-sr-tutti && "
            "make clean && make -j 8 && python3"
            " run_amarisoft.py ~/video/201_320x180_30fps_qp22_6min.mp4"
            f" {ue_indices}{dynamic_param} && tail -f /dev/null"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command=command,
                session_name="video_sr_tutti",
            )

            if result["success"]:
                self.logger.info("Video SR Tutti client started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"Failed to start video SR Tutti client: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR Tutti client startup: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def stop_video_sr_tutti_client(self) -> Dict[str, Any]:
        """
        Stop video SR Tutti client on amari.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Stopping video SR Tutti client on amari...")

        try:
            stop_cmd = (
                "tmux kill-session -t video_sr_tutti 2>/dev/null || true; "
                "sudo pkill -f 'video_sr_client' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="amari", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("Video SR Tutti client stopped successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Exception during video SR Tutti client cleanup: {e}"
            )
            return {"success": False, "error": str(e)}

    # Batch Operations
    def start_all_clients(
        self,
        file_transfer_ue_indices: str = "5,6,7,8",
        video_transcoding_ue_indices: str = "1,2",
        video_detection_ue_indices: str = "1,2",
        video_detection_smec_ue_indices: str = "1,2",
        video_sr_ue_indices: str = "1,2",
        video_sr_smec_ue_indices: str = "1,2",
        file_transfer_tutti_ue_indices: str = "5,6,7,8",
        video_transcoding_tutti_ue_indices: str = "1,2",
        video_detection_tutti_ue_indices: str = "1,2",
        video_sr_tutti_ue_indices: str = "1,2",
    ) -> Dict[str, Any]:
        """
        Start all application clients.

        Args:
            file_transfer_ue_indices: UE indices for file transfer clients
            video_transcoding_ue_indices: UE indices for video transcoding clients
            video_detection_ue_indices: UE indices for video detection clients
            video_detection_smec_ue_indices: UE indices for video detection SMEC clients
            video_sr_ue_indices: UE indices for video SR clients
            video_sr_smec_ue_indices: UE indices for video SR SMEC clients
            file_transfer_tutti_ue_indices: UE indices for file transfer Tutti clients
            video_transcoding_tutti_ue_indices: UE indices for video transcoding Tutti clients
            video_detection_tutti_ue_indices: UE indices for video detection Tutti clients
            video_sr_tutti_ue_indices: UE indices for video SR Tutti clients

        Returns:
            Dictionary containing results for all clients
        """
        self.logger.info("Starting all application clients...")

        results = {
            "file_transfer": self.start_file_transfer_client(
                file_transfer_ue_indices
            ),
            "file_transfer_smec": self.start_file_transfer_smec_client(
                file_transfer_ue_indices
            ),
            "file_transfer_tutti": self.start_file_transfer_tutti_client(
                file_transfer_tutti_ue_indices
            ),
            "video_transcoding": self.start_video_transcoding_client(
                video_transcoding_ue_indices
            ),
            "video_transcoding_smec": self.start_video_transcoding_smec_client(
                video_transcoding_ue_indices
            ),
            "video_transcoding_tutti": self.start_video_transcoding_tutti_client(
                video_transcoding_tutti_ue_indices
            ),
            "video_detection": self.start_video_detection_client(
                video_detection_ue_indices
            ),
            "video_detection_smec": self.start_video_detection_smec_client(
                video_detection_smec_ue_indices
            ),
            "video_detection_tutti": self.start_video_detection_tutti_client(
                video_detection_tutti_ue_indices
            ),
            "video_sr": self.start_video_sr_client(video_sr_ue_indices),
            "video_sr_smec": self.start_video_sr_smec_client(
                video_sr_smec_ue_indices
            ),
            "video_sr_tutti": self.start_video_sr_tutti_client(
                video_sr_tutti_ue_indices
            ),
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
            "file_transfer_smec": self.stop_file_transfer_smec_client(),
            "file_transfer_tutti": self.stop_file_transfer_tutti_client(),
            "video_transcoding": self.stop_video_transcoding_client(),
            "video_transcoding_smec": self.stop_video_transcoding_smec_client(),
            "video_transcoding_tutti": self.stop_video_transcoding_tutti_client(),
            "video_detection": self.stop_video_detection_client(),
            "video_detection_smec": self.stop_video_detection_smec_client(),
            "video_detection_tutti": self.stop_video_detection_tutti_client(),
            "video_sr": self.stop_video_sr_client(),
            "video_sr_smec": self.stop_video_sr_smec_client(),
            "video_sr_tutti": self.stop_video_sr_tutti_client(),
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
                "file_transfer_smec": False,
                "file_transfer_tutti": False,
                "video_transcoding": False,
                "video_transcoding_smec": False,
                "video_transcoding_tutti": False,
                "video_detection": False,
                "video_detection_smec": False,
                "video_detection_tutti": False,
                "video_sr": False,
                "video_sr_smec": False,
                "video_sr_tutti": False,
                "tmux_output": result.get("output", ""),
            }

            if result["success"] and result.get("output"):
                output = result["output"]
                status["file_transfer"] = "file_transfer:" in output
                status["file_transfer_smec"] = "file_transfer_smec:" in output
                status["file_transfer_tutti"] = "file_transfer_tutti:" in output
                status["video_transcoding"] = "video_transcoding:" in output
                status["video_transcoding_smec"] = (
                    "video_transcoding_smec:" in output
                )
                status["video_transcoding_tutti"] = (
                    "video_transcoding_tutti:" in output
                )
                status["video_detection"] = "video_detection:" in output
                status["video_detection_smec"] = (
                    "video_detection_smec:" in output
                )
                status["video_detection_tutti"] = (
                    "video_detection_tutti:" in output
                )
                status["video_sr"] = "video_sr:" in output
                status["video_sr_smec"] = "video_sr_smec:" in output
                status["video_sr_tutti"] = "video_sr_tutti:" in output

            return status

        except Exception as e:
            self.logger.error(f"Exception during status check: {e}")
            return {
                "file_transfer": False,
                "file_transfer_smec": False,
                "file_transfer_tutti": False,
                "video_transcoding": False,
                "video_transcoding_smec": False,
                "video_transcoding_tutti": False,
                "video_detection": False,
                "video_detection_smec": False,
                "video_detection_tutti": False,
                "video_sr": False,
                "video_sr_smec": False,
                "video_sr_tutti": False,
                "error": str(e),
            }
