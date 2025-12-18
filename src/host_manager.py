#!/usr/bin/env python3
"""
Host configuration manager for remote execution.

This module provides functionality to load host configurations from YAML files
and handle proxy connections for remote command execution.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .remote_executor import execute_background_command, execute_command


class HostManager:
    """Manages host configurations and provides easy access to remote hosts."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the host manager with a configuration file.

        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.hosts = self.config.get("hosts", {})
        self.defaults = self.config.get("defaults", {})
        self.proxy = self.config.get("proxy", {})

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
            logging.info(f"Loaded configuration from {self.config_file}")
            return config
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {self.config_file}")
            return {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML configuration: {e}")
            return {}

    def get_host_config(self, host_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific host.

        Args:
            host_name: Name of the host in the configuration

        Returns:
            Dictionary containing host configuration

        Raises:
            KeyError: If host is not found in configuration
        """
        if host_name not in self.hosts:
            raise KeyError(f"Host '{host_name}' not found in configuration")

        host_config = self.hosts[host_name].copy()

        # Apply defaults for missing values
        for key, value in self.defaults.items():
            if key not in host_config:
                host_config[key] = value

        # Expand tilde in paths
        if "key_filename" in host_config:
            host_config["key_filename"] = os.path.expanduser(
                host_config["key_filename"]
            )

        return host_config

    def list_hosts(self) -> Dict[str, str]:
        """
        List all available hosts with their descriptions.

        Returns:
            Dictionary mapping host names to descriptions
        """
        return {
            name: config.get("description", "No description")
            for name, config in self.hosts.items()
        }

    def execute_on_host(
        self,
        host_name: str,
        command: str,
        background: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute a command on a specific host using its configuration.

        Args:
            host_name: Name of the host in the configuration
            command: Command to execute
            background: Whether to execute command in background (default: True)
            **kwargs: Additional parameters to override host configuration

        Returns:
            Dictionary containing execution results
        """
        try:
            host_config = self.get_host_config(host_name)

            # Override with any provided kwargs
            host_config.update(kwargs)

            # Handle proxy command if present
            if "proxy_command" in host_config:
                # For proxy connections, we need to use a different approach
                # since Fabric doesn't directly support ProxyCommand
                # We'll use the proxy configuration to establish connection
                return self._execute_via_proxy(host_config, command, background)
            else:
                # Direct connection
                if background:
                    return execute_background_command(
                        command=command, **host_config
                    )
                else:
                    return execute_command(command=command, **host_config)

        except KeyError as e:
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": f"Host: {host_name}",
            }

    def _execute_via_proxy(
        self, host_config: Dict[str, Any], command: str, background: bool = True
    ) -> Dict[str, Any]:
        """
        Execute command via proxy connection.

        This is a simplified implementation. For complex proxy setups,
        you might need to use paramiko directly or configure SSH config.

        Args:
            host_config: Host configuration including proxy settings
            command: Command to execute
            background: Whether to execute command in background

        Returns:
            Dictionary containing execution results
        """
        # For now, we'll use the host configuration as-is
        # The proxy_command will be handled by the SSH client
        # if the SSH config is properly set up

        # Remove non-Fabric parameters from config
        config_for_fabric = host_config.copy()
        proxy_command = config_for_fabric.pop("proxy_command", None)
        forward_agent = config_for_fabric.pop("forward_agent", None)
        description = config_for_fabric.pop("description", None)
        paths = config_for_fabric.pop("paths", None)

        if proxy_command:
            logging.info(f"Using proxy command: {proxy_command}")
            # Note: Fabric doesn't directly support ProxyCommand
            # You might need to set up SSH config file or use paramiko directly

        if forward_agent:
            logging.info(f"Forward agent: {forward_agent}")
            # Note: Fabric doesn't directly support forward_agent
            # You might need to configure SSH config file

        if description:
            logging.info(f"Host description: {description}")

        # Special handling for amari host
        use_ssh_config = False
        if (
            config_for_fabric.get("host") == "192.168.0.15"
            or host_config.get("host") == "192.168.0.15"
        ):
            use_ssh_config = True
            logging.info("Using SSH config for amari host")

        if background:
            return execute_background_command(
                command=command,
                use_ssh_config=use_ssh_config,
                **config_for_fabric,
            )
        else:
            return execute_command(
                command=command,
                use_ssh_config=use_ssh_config,
                **config_for_fabric,
            )

    def execute_on_all_hosts(
        self, command: str, exclude_hosts: Optional[list] = None, **kwargs: Any
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute a command on all configured hosts.

        Args:
            command: Command to execute
            exclude_hosts: List of host names to exclude
            **kwargs: Additional parameters to override host configurations

        Returns:
            Dictionary mapping host names to execution results
        """
        exclude_hosts = exclude_hosts or []
        results = {}

        for host_name in self.hosts:
            if host_name not in exclude_hosts:
                results[host_name] = self.execute_on_host(
                    host_name=host_name, command=command, **kwargs
                )

        return results

    def test_connections(self) -> Dict[str, bool]:
        """
        Test connections to all configured hosts.

        Returns:
            Dictionary mapping host names to connection status
        """
        results = {}

        for host_name in self.hosts:
            try:
                result = self.execute_on_host(
                    host_name=host_name,
                    command="echo 'Connection test successful'",
                    background=False,
                )
                results[host_name] = result["success"]
            except Exception as e:
                logging.error(f"Connection test failed for {host_name}: {e}")
                results[host_name] = False

        return results


# Convenience functions for easy access
def get_host_manager(config_file: str = "hosts_config.yaml") -> HostManager:
    """Get a host manager instance."""
    return HostManager(config_file)


def execute_on_host(
    host_name: str,
    command: str,
    config_file: str = "hosts_config.yaml",
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Convenience function to execute a command on a specific host.

    Args:
        host_name: Name of the host in the configuration
        command: Command to execute
        config_file: Path to configuration file
        **kwargs: Additional parameters

    Returns:
        Dictionary containing execution results
    """
    manager = HostManager(config_file)
    return manager.execute_on_host(host_name, command, **kwargs)
