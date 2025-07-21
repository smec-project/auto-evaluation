#!/usr/bin/env python3
"""
Remote command execution module using Fabric.

This module provides functionality to connect to remote hosts and execute
commands in the background using Fabric library.
"""

import logging
import os
from typing import Optional, Dict, Any
from fabric import Connection
from fabric.runners import Result


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
    use_ssh_config: bool = True,
    **kwargs: Any
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
        use_ssh_config: Whether to use SSH config file (default: True)
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
    result = {
        'success': False,
        'exit_code': None,
        'output': '',
        'error': '',
        'connection_info': f'{user}@{host}:{port}' if user else f'{host}:{port}'
    }
    
    try:
        # Check if we should use SSH config
        ssh_config_host = None
        if use_ssh_config:
            # For amari, check if it's in SSH config
            if host == "192.168.0.15" or host.lower() == "amari":
                ssh_config_host = get_ssh_config_host("amari")
                if ssh_config_host:
                    host = ssh_config_host
                    logging.info(f"Using SSH config for host: {host}")
        
        # Create connection parameters
        connect_kwargs = {}
        
        if key_filename and not ssh_config_host:
            connect_kwargs['key_filename'] = key_filename
        if password:
            connect_kwargs['password'] = password
            
        # Add other kwargs
        connect_kwargs.update(kwargs)
            
        # Establish connection
        if ssh_config_host:
            # Use SSH config for connection
            connection = Connection(host)
        else:
            connection = Connection(
                host=host,
                user=user,
                port=port,
                connect_kwargs=connect_kwargs
            )
        
        # Test connection
        connection.open()
        
        logging.info(f"Executing command on {result['connection_info']}: {command}")
        
        # Execute the command
        execution_result: Result = connection.run(
            command,
            hide=True,
            warn=True
        )
        
        result['exit_code'] = execution_result.exited
        result['output'] = execution_result.stdout.strip()
        
        if execution_result.exited == 0:
            result['success'] = True
            logging.info(f"Command executed successfully")
        else:
            result['error'] = execution_result.stderr or "Command execution failed"
            logging.error(f"Command execution failed: {result['error']}")
            
    except Exception as e:
        result['error'] = str(e)
        logging.error(f"Connection or execution error: {e}")
        
    finally:
        if connection:
            try:
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
    use_ssh_config: bool = True,
    session_name: Optional[str] = None,
    **kwargs: Any
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
        use_ssh_config: Whether to use SSH config file (default: True)
        session_name: Custom tmux session name (optional)
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
    result = {
        'success': False,
        'pid': None,
        'output': '',
        'error': '',
        'connection_info': f'{user}@{host}:{port}' if user else f'{host}:{port}'
    }
    
    try:
        # Check if we should use SSH config
        ssh_config_host = None
        if use_ssh_config:
            # For amari, check if it's in SSH config
            if host == "192.168.0.15" or host.lower() == "amari":
                ssh_config_host = get_ssh_config_host("amari")
                if ssh_config_host:
                    host = ssh_config_host
                    logging.info(f"Using SSH config for host: {host}")
        
        # Create connection parameters
        connect_kwargs = {}
        
        if key_filename and not ssh_config_host:
            connect_kwargs['key_filename'] = key_filename
        if password:
            connect_kwargs['password'] = password
            
        # Add other kwargs
        connect_kwargs.update(kwargs)
            
        # Establish connection
        if ssh_config_host:
            # Use SSH config for connection
            connection = Connection(host)
        else:
            connection = Connection(
                host=host,
                user=user,
                port=port,
                connect_kwargs=connect_kwargs
            )
        
        # Test connection
        connection.open()
        
        # Execute command in background using tmux
        # Create a new tmux session to run the command
        if not session_name:
            session_name = f"bg_session_{hash(command) % 10000}"
        background_cmd = f"tmux new-session -d -s {session_name} '{command}' && tmux list-sessions | grep {session_name} | cut -d: -f1"
        
        logging.info(f"Executing background command on {result['connection_info']}: {command}")
        
        # Execute the command
        execution_result: Result = connection.run(
            background_cmd,
            hide=True,
            warn=True
        )
        
        if execution_result.exited == 0:
            result['success'] = True
            result['output'] = execution_result.stdout.strip()
            # Store tmux session name instead of PID
            if result['output']:
                result['session_name'] = result['output']
                logging.info(f"Background process started in tmux session: {result['output']}")
                # Try to get the actual PID of the process in tmux session
                try:
                    pid_cmd = f"tmux list-panes -s {result['output']} -F '#{{pane_pid}}'"
                    pid_result = connection.run(pid_cmd, hide=True, warn=True)
                    if pid_result.exited == 0 and pid_result.stdout.strip():
                        result['pid'] = int(pid_result.stdout.strip())
                        logging.info(f"Process PID in tmux: {result['pid']}")
                except (ValueError, Exception) as e:
                    logging.debug(f"Could not get PID from tmux session: {e}")
            else:
                logging.warning("No tmux session name returned")
        else:
            result['error'] = execution_result.stderr or "Command execution failed"
            logging.error(f"Command execution failed: {result['error']}")
            
    except Exception as e:
        result['error'] = str(e)
        logging.error(f"Connection or execution error: {e}")
        
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")
                
    return result
