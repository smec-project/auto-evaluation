#!/usr/bin/env python3
"""
Remote command execution module using Fabric.

This module provides functionality to connect to remote hosts and execute
commands in the background using Fabric library.
"""

import logging
import os
import threading
from contextlib import nullcontext
from typing import Optional, Dict, Any
from fabric import Connection
from fabric.runners import Result

# Cache persistent SSH connections to avoid repeated handshakes / firewall limits
_connection_pool: Dict[str, Connection] = {}
# Per-connection locks to serialize reuse on the same host/user/key
_connection_locks: Dict[str, threading.Lock] = {}
# Global lock to protect lock creation
_pool_lock = threading.Lock()


def _get_conn_lock(conn_key: str) -> threading.Lock:
    with _pool_lock:
        lock = _connection_locks.get(conn_key)
        if lock is None:
            lock = threading.Lock()
            _connection_locks[conn_key] = lock
        return lock


def get_ssh_config_host(host_name: str) -> Optional[str]:
    """
    Check if a host is configured in SSH config file.

    Args:
        host_name: Name of the host to check

    Returns:
        Host name if found in SSH config, None otherwise
    """
    try:
        from paramiko import SSHConfig

        ssh_config = SSHConfig()
        ssh_config_file = os.path.expanduser("~/.ssh/config")

        if os.path.exists(ssh_config_file):
            with open(ssh_config_file) as f:
                ssh_config.parse(f)

            # Check if host exists in SSH config
            if ssh_config.lookup(host_name):
                return host_name
    except Exception as e:
        logging.debug(f"Error checking SSH config: {e}")

    return None


def execute_command(
    host: str,
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    key_filename: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    connect_timeout: int = 60,
    banner_timeout: int = 60,
    auth_timeout: int = 60,
    use_ssh_config: bool = True,
    reuse_connection: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Connect to a remote host and execute a command in the foreground.

    Args:
        host: Remote host IP address or hostname
        command: Command to execute
        user: Username for SSH connection (optional)
        port: SSH port (default: 22)
        key_filename: Path to SSH private key file (optional)
        password: SSH password (optional, not recommended for security)
        timeout: Connection timeout in seconds (default: 30)
        connect_timeout: SSH TCP connect timeout (default: 60)
        banner_timeout: SSH banner wait timeout (default: 60)
        auth_timeout: SSH auth timeout (default: 60)
        use_ssh_config: Whether to use SSH config file (default: True)
        reuse_connection: Whether to reuse a persistent SSH connection (default: True)
        **kwargs: Additional connection parameters

    Returns:
        Dictionary containing execution results with keys:
        - success: Boolean indicating if command was executed successfully
        - exit_code: Exit code of the command
        - output: Command output (stdout)
        - error: Error output (stderr) if execution failed
        - connection_info: Information about the connection

    Raises:
        Exception: If connection or command execution fails
    """
    connection = None
    stored_in_pool = False
    result = {
        "success": False,
        "exit_code": None,
        "output": "",
        "error": "",
        "connection_info": (
            f"{user}@{host}:{port}" if user else f"{host}:{port}"
        ),
    }

    try:
        # Check if we should use SSH config
        ssh_config_host = None
        resolved_host = host
        if use_ssh_config:
            # For amari, check if it's in SSH config
            if host == "192.168.0.15" or host.lower() == "amari":
                ssh_config_host = get_ssh_config_host("amari")
                if ssh_config_host:
                    resolved_host = ssh_config_host
                    logging.info(f"Using SSH config for host: {resolved_host}")

        # Create connection parameters
        connect_kwargs = {}

        if key_filename and not ssh_config_host:
            connect_kwargs["key_filename"] = key_filename
        if password:
            connect_kwargs["password"] = password

        # Add other kwargs
        connect_kwargs.update(kwargs)

        # Propagate timeouts to paramiko (Fabric passes these via connect_kwargs)
        connect_kwargs.setdefault("banner_timeout", banner_timeout)
        connect_kwargs.setdefault("auth_timeout", auth_timeout)

        # Propagate timeouts to paramiko (Fabric passes these via connect_kwargs)
        connect_kwargs.setdefault("banner_timeout", banner_timeout)
        connect_kwargs.setdefault("auth_timeout", auth_timeout)

        # Build a cache key for connection reuse
        conn_key = (
            f"{resolved_host}|{user or ''}|{port}|{key_filename or ''}|"
            f"{ssh_config_host or ''}"
        )

        lock_ctx = (
            _get_conn_lock(conn_key) if reuse_connection else nullcontext()
        )

        with lock_ctx:
            try:
                # Try to reuse an existing open connection
                if reuse_connection and conn_key in _connection_pool:
                    connection = _connection_pool[conn_key]
                    try:
                        if not connection.is_connected:
                            connection.open()
                    except Exception as e:
                        logging.warning(
                            f"Reopening SSH connection failed, recreating: {e}"
                        )
                        try:
                            connection.close()
                        except Exception:
                            pass
                        _connection_pool.pop(conn_key, None)
                        connection = None

                # Establish new connection if needed
                if connection is None:
                    if ssh_config_host:
                        # Use SSH config for connection
                        connection = Connection(
                            resolved_host,
                            connect_timeout=connect_timeout,
                            connect_kwargs=connect_kwargs,
                        )
                    else:
                        connection = Connection(
                            host=resolved_host,
                            user=user,
                            port=port,
                            connect_timeout=connect_timeout,
                            connect_kwargs=connect_kwargs,
                        )

                    # Test connection
                    connection.open()

                    if reuse_connection:
                        _connection_pool[conn_key] = connection
                        stored_in_pool = True

                # Update connection info with the resolved host
                result["connection_info"] = (
                    f"{user}@{resolved_host}:{port}"
                    if user
                    else f"{resolved_host}:{port}"
                )

                logging.info(
                    f"Executing command on {result['connection_info']}:"
                    f" {command}"
                )

                # Execute the command
                execution_result: Result = connection.run(
                    command, hide=True, warn=True
                )

                result["exit_code"] = execution_result.exited
                result["output"] = execution_result.stdout.strip()

                if execution_result.exited == 0:
                    result["success"] = True
                    logging.info("Command executed successfully")
                else:
                    result["error"] = (
                        execution_result.stderr or "Command execution failed"
                    )
                    logging.error(
                        f"Command execution failed: {result['error']}"
                    )
            finally:
                if connection:
                    try:
                        if not reuse_connection or not stored_in_pool:
                            connection.close()
                    except Exception as e:
                        logging.warning(f"Error closing connection: {e}")

    except Exception as e:
        result["error"] = str(e)
        logging.error(f"Connection or execution error: {e}")

    finally:
        if connection:
            try:
                if not reuse_connection or not stored_in_pool:
                    connection.close()
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")

    return result


def execute_background_command(
    host: str,
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    key_filename: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    connect_timeout: int = 60,
    banner_timeout: int = 60,
    auth_timeout: int = 60,
    use_ssh_config: bool = True,
    session_name: Optional[str] = None,
    reuse_connection: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Connect to a remote host and execute a command in the background.

    Args:
        host: Remote host IP address or hostname
        command: Command to execute in the background
        user: Username for SSH connection (optional)
        port: SSH port (default: 22)
        key_filename: Path to SSH private key file (optional)
        password: SSH password (optional, not recommended for security)
        timeout: Connection timeout in seconds (default: 30)
        connect_timeout: SSH TCP connect timeout (default: 60)
        banner_timeout: SSH banner wait timeout (default: 60)
        auth_timeout: SSH auth timeout (default: 60)
        use_ssh_config: Whether to use SSH config file (default: True)
        session_name: Custom tmux session name (optional)
        reuse_connection: Whether to reuse a persistent SSH connection (default: True)
        **kwargs: Additional connection parameters

    Returns:
        Dictionary containing execution results with keys:
        - success: Boolean indicating if command was executed successfully
        - pid: Process ID of the background process (if available)
        - output: Any immediate output from the command
        - error: Error message if execution failed
        - connection_info: Information about the connection

    Raises:
        Exception: If connection or command execution fails
    """
    connection = None
    stored_in_pool = False
    result = {
        "success": False,
        "pid": None,
        "output": "",
        "error": "",
        "connection_info": (
            f"{user}@{host}:{port}" if user else f"{host}:{port}"
        ),
    }

    try:
        # Check if we should use SSH config
        ssh_config_host = None
        resolved_host = host
        if use_ssh_config:
            # For amari, check if it's in SSH config
            if host == "192.168.0.15" or host.lower() == "amari":
                ssh_config_host = get_ssh_config_host("amari")
                if ssh_config_host:
                    resolved_host = ssh_config_host
                    logging.info(f"Using SSH config for host: {resolved_host}")

        # Create connection parameters
        connect_kwargs = {}

        if key_filename and not ssh_config_host:
            connect_kwargs["key_filename"] = key_filename
        if password:
            connect_kwargs["password"] = password

        # Add other kwargs
        connect_kwargs.update(kwargs)

        # Build a cache key for connection reuse
        conn_key = (
            f"{resolved_host}|{user or ''}|{port}|{key_filename or ''}|"
            f"{ssh_config_host or ''}"
        )

        lock_ctx = (
            _get_conn_lock(conn_key) if reuse_connection else nullcontext()
        )

        with lock_ctx:
            try:
                # Try to reuse an existing open connection
                if reuse_connection and conn_key in _connection_pool:
                    connection = _connection_pool[conn_key]
                    try:
                        if not connection.is_connected:
                            connection.open()
                    except Exception as e:
                        logging.warning(
                            f"Reopening SSH connection failed, recreating: {e}"
                        )
                        try:
                            connection.close()
                        except Exception:
                            pass
                        _connection_pool.pop(conn_key, None)
                        connection = None

                # Establish new connection if needed
                if connection is None:
                    if ssh_config_host:
                        # Use SSH config for connection
                        connection = Connection(
                            resolved_host,
                            connect_timeout=connect_timeout,
                            connect_kwargs=connect_kwargs,
                        )
                    else:
                        connection = Connection(
                            host=resolved_host,
                            user=user,
                            port=port,
                            connect_timeout=connect_timeout,
                            connect_kwargs=connect_kwargs,
                        )

                    # Test connection
                    connection.open()

                    if reuse_connection:
                        _connection_pool[conn_key] = connection
                        stored_in_pool = True

                # Update connection info with the resolved host
                result["connection_info"] = (
                    f"{user}@{resolved_host}:{port}"
                    if user
                    else f"{resolved_host}:{port}"
                )

                # Execute command in background using tmux
                # Create a new tmux session to run the command
                if not session_name:
                    session_name = f"bg_session_{hash(command) % 10000}"
                background_cmd = (
                    f"tmux new-session -d -s {session_name} '{command}' && tmux"
                    f" list-sessions | grep {session_name} | cut -d: -f1"
                )

                logging.info(
                    "Executing background command on %s: %s",
                    result["connection_info"],
                    command,
                )

                # Execute the command
                execution_result: Result = connection.run(
                    background_cmd, hide=True, warn=True
                )

                if execution_result.exited == 0:
                    result["success"] = True
                    result["output"] = execution_result.stdout.strip()
                    # Store tmux session name instead of PID
                    if result["output"]:
                        result["session_name"] = result["output"]
                        logging.info(
                            "Background process started in tmux session: %s",
                            result["output"],
                        )
                        # Try to get the actual PID of the process in tmux session
                        try:
                            pid_cmd = (
                                f"tmux list-panes -s {result['output']} -F"
                                " '#{pane_pid}'"
                            )
                            pid_result = connection.run(
                                pid_cmd, hide=True, warn=True
                            )
                            if (
                                pid_result.exited == 0
                                and pid_result.stdout.strip()
                            ):
                                result["pid"] = int(pid_result.stdout.strip())
                                logging.info(
                                    "Process PID in tmux: %s", result["pid"]
                                )
                        except (ValueError, Exception) as e:
                            logging.debug(
                                "Could not get PID from tmux session: %s", e
                            )
                    else:
                        logging.warning("No tmux session name returned")
                else:
                    result["error"] = (
                        execution_result.stderr or "Command execution failed"
                    )
                    logging.error(
                        "Command execution failed: %s", result["error"]
                    )
            finally:
                if connection:
                    try:
                        if not reuse_connection or not stored_in_pool:
                            connection.close()
                    except Exception as e:
                        logging.warning(f"Error closing connection: {e}")

    except Exception as e:
        result["error"] = str(e)
        logging.error(f"Connection or execution error: {e}")

    finally:
        if connection:
            try:
                if not reuse_connection or not stored_in_pool:
                    connection.close()
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")

    return result


def close_all_connections():
    """Close and clear all cached SSH connections."""
    for key, conn in list(_connection_pool.items()):
        try:
            conn.close()
        except Exception as e:
            logging.debug(f"Error closing connection {key}: {e}")
        finally:
            _connection_pool.pop(key, None)
