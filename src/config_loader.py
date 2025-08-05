#!/usr/bin/env python3
"""
Configuration Loader

This module handles loading and processing experiment configuration files.
It reads JSON configuration files and provides methods to extract UE indices
and calculate server instance counts.
"""

import json
import logging
import os
from typing import Dict, Any, Tuple


class ConfigLoader:
    """Configuration loader for experiment settings."""

    def __init__(self, config_file: str):
        """
        Initialize the configuration loader.

        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self.config_data = {}
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> bool:
        """
        Load configuration from JSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                self.logger.error(
                    f"Configuration file not found: {self.config_file}"
                )
                return False

            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)

            self.logger.info(f"Configuration loaded from: {self.config_file}")
            self.logger.info(f"Configuration: {self.config_data}")
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading configuration file: {e}")
            return False

    def get_transcoding_ue_indices(self) -> str:
        """
        Get UE indices for video transcoding applications.

        Returns:
            Comma-separated UE indices string
        """
        return self.config_data.get("transcoding_ue_indices", "")

    def get_file_transfer_ue_indices(self) -> str:
        """
        Get UE indices for file transfer applications.

        Returns:
            Comma-separated UE indices string
        """
        return self.config_data.get("file_transfer_ue_indices", "")

    def get_video_detection_ue_indices(self) -> str:
        """
        Get UE indices for video detection applications.

        Returns:
            Comma-separated UE indices string
        """
        return self.config_data.get("video_detection_ue_indices", "")

    def get_pmec_ue_indices(self) -> str:
        """
        Get UE indices for PMEC controller.

        Returns:
            Comma-separated UE indices string
        """
        return self.config_data.get("pmec_ue_indices", "")

    def get_video_sr_ue_indices(self) -> str:
        """
        Get UE indices for video SR applications.

        Returns:
            Comma-separated UE indices string
        """
        return self.config_data.get("video_sr_ue_indices", "")

    def get_num_ues(self) -> int:
        """
        Get the number of UE namespaces configured.

        Returns:
            Number of UE namespaces (default: 8)
        """
        return self.config_data.get("num_ues", 8)

    def calculate_server_instances(self, ue_indices: str) -> int:
        """
        Calculate the number of server instances based on UE indices.

        For video transcoding servers, the instance count is typically
        equal to the number of UE indices.

        Args:
            ue_indices: Comma-separated UE indices string

        Returns:
            Number of server instances to create
        """
        try:
            # Split by comma, strip whitespace, and count non-empty entries
            indices_list = [
                idx.strip() for idx in ue_indices.split(",") if idx.strip()
            ]
            instance_count = len(indices_list)

            # Ensure at least 1 instance
            if instance_count == 0:
                self.logger.warning(
                    "No valid UE indices found, defaulting to 1 instance"
                )
                return 1

            self.logger.info(
                f"Calculated {instance_count} server instances for UE indices:"
                f" {ue_indices}"
            )
            return instance_count

        except Exception as e:
            self.logger.error(f"Error calculating server instances: {e}")
            return 1

    def get_transcoding_server_instances(self) -> int:
        """
        Get the number of video transcoding server instances.

        Returns:
            Number of transcoding server instances
        """
        transcoding_ues = self.get_transcoding_ue_indices()
        return self.calculate_server_instances(transcoding_ues)

    def get_video_detection_server_instances(self) -> int:
        """
        Get the number of video detection server instances.

        Returns:
            Number of video detection server instances
        """
        detection_ues = self.get_video_detection_ue_indices()
        return self.calculate_server_instances(detection_ues)

    def get_video_sr_server_instances(self) -> int:
        """
        Get the number of video SR server instances.

        Returns:
            Number of video SR server instances
        """
        video_sr_ues = self.get_video_sr_ue_indices()
        return self.calculate_server_instances(video_sr_ues)

    def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration parameters.

        Returns:
            Dictionary containing all configuration parameters
        """
        transcoding_ues = self.get_transcoding_ue_indices()
        file_transfer_ues = self.get_file_transfer_ue_indices()
        video_detection_ues = self.get_video_detection_ue_indices()
        video_sr_ues = self.get_video_sr_ue_indices()
        pmec_ues = self.get_pmec_ue_indices()

        return {
            "transcoding_ue_indices": transcoding_ues,
            "file_transfer_ue_indices": file_transfer_ues,
            "video_detection_ue_indices": video_detection_ues,
            "video_sr_ue_indices": video_sr_ues,
            "pmec_ue_indices": pmec_ues,
            "transcoding_server_instances": self.calculate_server_instances(
                transcoding_ues
            ),
            "video_detection_server_instances": self.calculate_server_instances(
                video_detection_ues
            ),
            "video_sr_server_instances": self.calculate_server_instances(
                video_sr_ues
            ),
            "raw_config": self.config_data.copy(),
        }

    def print_config_summary(self):
        """Print a summary of the loaded configuration."""
        config = self.get_all_config()

        self.logger.info("=" * 50)
        self.logger.info("EXPERIMENT CONFIGURATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Configuration file: {self.config_file}")
        self.logger.info(
            f"Video transcoding UE indices: {config['transcoding_ue_indices']}"
        )
        self.logger.info(
            "Video detection UE indices:"
            f" {config['video_detection_ue_indices']}"
        )
        self.logger.info(
            f"Video SR UE indices: {config['video_sr_ue_indices']}"
        )
        self.logger.info(
            f"File transfer UE indices: {config['file_transfer_ue_indices']}"
        )
        self.logger.info(
            f"PMEC controller UE indices: {config['pmec_ue_indices']}"
        )
        self.logger.info(
            "Video transcoding server instances:"
            f" {config['transcoding_server_instances']}"
        )
        self.logger.info(
            "Video detection server instances:"
            f" {config['video_detection_server_instances']}"
        )
        self.logger.info(
            f"Video SR server instances: {config['video_sr_server_instances']}"
        )
        self.logger.info("=" * 50)


def load_experiment_config(config_file: str) -> ConfigLoader:
    """
    Convenience function to load experiment configuration.

    Args:
        config_file: Path to the JSON configuration file

    Returns:
        ConfigLoader instance

    Raises:
        Exception: If configuration loading or validation fails
    """
    loader = ConfigLoader(config_file)

    return loader
