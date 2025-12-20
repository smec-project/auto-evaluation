#!/usr/bin/env python3
"""
Get Results Module

This module provides functions to retrieve experiment results from remote hosts.
"""

import logging
import os
import yaml
from typing import Dict, Any
from fabric import Connection


def load_hosts_config(config_file: str = "hosts_config.yaml") -> Dict[str, Any]:
    """
    Load hosts configuration from YAML file.

    Args:
        config_file: Path to the hosts configuration YAML file

    Returns:
        Dictionary containing hosts configuration

    Raises:
        FileNotFoundError: If configuration file is not found
        yaml.YAMLError: If YAML parsing fails
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"Hosts configuration file not found: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_ran_logs(
    local_folder: str, hosts_config_file: str = "hosts_config.yaml"
) -> bool:
    """
    Pull RAN controller logs from ran_server.

    This function retrieves the controller.log file from the ran_server host
    at {srsRAN_path}/smec_controller/controller.log and saves it to the specified
    local folder with the same filename (controller.log).

    Args:
        local_folder: Local folder path where controller.log should be saved
        hosts_config_file: Path to the hosts configuration YAML file

    Returns:
        True if file was successfully retrieved, False otherwise

    Example:
        >>> get_ran_logs("./results")
        True
        # File saved to ./results/controller.log
    """
    logger = logging.getLogger(__name__)
    connection = None

    try:
        # Load hosts configuration
        config = load_hosts_config(hosts_config_file)
        ran_server_config = config["hosts"]["ran_server"]

        # Get srsRAN_path from configuration
        srsran_path = ran_server_config["paths"]["srsRAN_path"]
        remote_file = f"{srsran_path}/smec_controller/controller.log"

        # Create connection parameters
        connect_kwargs = {}
        if "key_filename" in ran_server_config:
            key_file = os.path.expanduser(ran_server_config["key_filename"])
            connect_kwargs["key_filename"] = [key_file]

        # Build connection config
        conn_config = {
            "host": ran_server_config["host"],
            "user": ran_server_config["user"],
            "port": ran_server_config.get("port", 22),
            "connect_kwargs": connect_kwargs,
        }

        # Handle proxy/gateway if specified
        if "proxy_command" in ran_server_config:
            # Extract proxy host from proxy_command
            # Format: "ssh user@proxy_host -W %h:%p"
            proxy_command = ran_server_config["proxy_command"]
            if "ssh" in proxy_command and "@" in proxy_command:
                # Parse proxy user and host
                parts = proxy_command.split()
                for part in parts:
                    if "@" in part:
                        proxy_user, proxy_host = part.split("@")
                        # Create gateway connection
                        gateway_kwargs = {}
                        if "key_filename" in ran_server_config:
                            key_file = os.path.expanduser(
                                ran_server_config["key_filename"]
                            )
                            gateway_kwargs["key_filename"] = [key_file]

                        gateway = Connection(
                            host=proxy_host,
                            user=proxy_user,
                            connect_kwargs=gateway_kwargs,
                        )
                        conn_config["gateway"] = gateway
                        break

        # Create connection
        connection = Connection(**conn_config)
        connection.open()

        logger.info(f"Connected to ran_server: {ran_server_config['host']}")
        logger.info(f"Retrieving file: {remote_file}")

        # Create local directory if it doesn't exist
        if not os.path.exists(local_folder):
            os.makedirs(local_folder, exist_ok=True)
            logger.info(f"Created local directory: {local_folder}")

        # Build local file path
        local_path = os.path.join(local_folder, "controller.log")

        # Pull the file from remote host
        connection.get(remote_file, local_path)

        logger.info(f"Successfully retrieved controller.log to {local_path}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error retrieving RAN logs: {e}")
        return False
    finally:
        if connection:
            try:
                connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def get_scheduler_logs(
    local_folder: str, hosts_config_file: str = "hosts_config.yaml"
) -> bool:
    """
    Pull scheduler logs from edge_server.

    This function retrieves the scheduler.log file from the edge_server host
    at {edge_manager_path}/scheduler.log and saves it to the specified local folder
    with the same filename (scheduler.log).

    Args:
        local_folder: Local folder path where scheduler.log should be saved
        hosts_config_file: Path to the hosts configuration YAML file

    Returns:
        True if file was successfully retrieved, False otherwise

    Example:
        >>> get_scheduler_logs("./results")
        True
        # File saved to ./results/scheduler.log
    """
    logger = logging.getLogger(__name__)
    connection = None

    try:
        # Load hosts configuration
        config = load_hosts_config(hosts_config_file)
        edge_server_config = config["hosts"]["edge_server"]

        # Get edge_manager_path from configuration
        edge_manager_path = edge_server_config["paths"]["edge_manager_path"]
        remote_file = f"{edge_manager_path}/scheduler.log"

        # Create connection parameters
        connect_kwargs = {}
        if "key_filename" in edge_server_config:
            key_file = os.path.expanduser(edge_server_config["key_filename"])
            connect_kwargs["key_filename"] = [key_file]

        # Build connection config
        conn_config = {
            "host": edge_server_config["host"],
            "user": edge_server_config["user"],
            "port": edge_server_config.get("port", 22),
            "connect_kwargs": connect_kwargs,
        }

        # Handle proxy/gateway if specified
        if "proxy_command" in edge_server_config:
            # Extract proxy host from proxy_command
            # Format: "ssh user@proxy_host -W %h:%p"
            proxy_command = edge_server_config["proxy_command"]
            if "ssh" in proxy_command and "@" in proxy_command:
                # Parse proxy user and host
                parts = proxy_command.split()
                for part in parts:
                    if "@" in part:
                        proxy_user, proxy_host = part.split("@")
                        # Create gateway connection
                        gateway_kwargs = {}
                        if "key_filename" in edge_server_config:
                            key_file = os.path.expanduser(
                                edge_server_config["key_filename"]
                            )
                            gateway_kwargs["key_filename"] = [key_file]

                        gateway = Connection(
                            host=proxy_host,
                            user=proxy_user,
                            connect_kwargs=gateway_kwargs,
                        )
                        conn_config["gateway"] = gateway
                        break

        # Create connection
        connection = Connection(**conn_config)
        connection.open()

        logger.info(f"Connected to edge_server: {edge_server_config['host']}")
        logger.info(f"Retrieving file: {remote_file}")

        # Create local directory if it doesn't exist
        if not os.path.exists(local_folder):
            os.makedirs(local_folder, exist_ok=True)
            logger.info(f"Created local directory: {local_folder}")

        # Build local file path
        local_path = os.path.join(local_folder, "scheduler.log")

        # Pull the file from remote host
        connection.get(remote_file, local_path)

        logger.info(f"Successfully retrieved scheduler.log to {local_path}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error retrieving scheduler logs: {e}")
        return False
    finally:
        if connection:
            try:
                connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def get_server_results(
    local_folder: str, method: str, hosts_config_file: str = "hosts_config.yaml"
) -> bool:
    """
    Pull server results from edge_server for all applications.

    This function retrieves result files from the edge_server for four applications:
    file-transfer, video-od, video-sr, and video-transcoding. Each application has
    a server folder with result/results subfolder containing output files.

    Local directory structure created:
        local_folder/
          ├── file-transfer/
          │   └── server/
          │       └── (result files)
          ├── video-od/
          │   └── server/
          │       └── (result files)
          ├── video-sr/
          │   └── server/
          │       └── (result files)
          └── video-transcoding/
              └── server/
                  └── (result files)

    Args:
        local_folder: Local folder path where results should be saved
        method: Method name (subfolder under apps_path)
        hosts_config_file: Path to the hosts configuration YAML file

    Returns:
        True if all files were successfully retrieved, False otherwise

    Example:
        >>> get_server_results("./results", "smec")
        True
    """
    logger = logging.getLogger(__name__)
    connection = None

    # Four applications to process
    applications = [
        "file-transfer",
        "video-od",
        "video-sr",
        "video-transcoding",
    ]

    try:
        # Load hosts configuration
        config = load_hosts_config(hosts_config_file)
        edge_server_config = config["hosts"]["edge_server"]

        # Get apps_path from configuration
        apps_path = edge_server_config["paths"]["apps_path"]

        # Create connection parameters
        connect_kwargs = {}
        if "key_filename" in edge_server_config:
            key_file = os.path.expanduser(edge_server_config["key_filename"])
            connect_kwargs["key_filename"] = [key_file]

        # Build connection config
        conn_config = {
            "host": edge_server_config["host"],
            "user": edge_server_config["user"],
            "port": edge_server_config.get("port", 22),
            "connect_kwargs": connect_kwargs,
        }

        # Handle proxy/gateway if specified
        if "proxy_command" in edge_server_config:
            # Extract proxy host from proxy_command
            # Format: "ssh user@proxy_host -W %h:%p"
            proxy_command = edge_server_config["proxy_command"]
            if "ssh" in proxy_command and "@" in proxy_command:
                # Parse proxy user and host
                parts = proxy_command.split()
                for part in parts:
                    if "@" in part:
                        proxy_user, proxy_host = part.split("@")
                        # Create gateway connection
                        gateway_kwargs = {}
                        if "key_filename" in edge_server_config:
                            key_file = os.path.expanduser(
                                edge_server_config["key_filename"]
                            )
                            gateway_kwargs["key_filename"] = [key_file]

                        gateway = Connection(
                            host=proxy_host,
                            user=proxy_user,
                            connect_kwargs=gateway_kwargs,
                        )
                        conn_config["gateway"] = gateway
                        break

        # Create connection
        connection = Connection(**conn_config)
        connection.open()

        logger.info(f"Connected to edge_server: {edge_server_config['host']}")

        # Create base local directory if it doesn't exist
        if not os.path.exists(local_folder):
            os.makedirs(local_folder, exist_ok=True)
            logger.info(f"Created local directory: {local_folder}")

        # Process each application
        all_success = True
        for app in applications:
            try:
                logger.info(f"Processing application: {app}")

                # Remote path for this application
                remote_app_path = f"{apps_path}/{method}/{app}/server"

                # Check if result or results folder exists
                check_result_cmd = (
                    f"[ -d '{remote_app_path}/result' ] && echo 'result' || (["
                    f" -d '{remote_app_path}/results' ] && echo 'results' ||"
                    " echo 'none')"
                )
                result_check = connection.run(
                    check_result_cmd, hide=True, warn=True
                )

                if result_check.exited != 0:
                    logger.warning(f"Could not check result folder for {app}")
                    all_success = False
                    continue

                result_folder_name = result_check.stdout.strip()

                if result_folder_name == "none":
                    logger.warning(
                        f"No result/results folder found for {app} at"
                        f" {remote_app_path}"
                    )
                    all_success = False
                    continue

                # Remote result path
                remote_result_path = f"{remote_app_path}/{result_folder_name}"
                logger.info(
                    f"Found {result_folder_name} folder at {remote_result_path}"
                )

                # Create local directory structure: local_folder/app/server/
                local_app_server_path = os.path.join(
                    local_folder, app, "server"
                )
                if not os.path.exists(local_app_server_path):
                    os.makedirs(local_app_server_path, exist_ok=True)
                    logger.info(
                        f"Created local directory: {local_app_server_path}"
                    )

                # Get list of files in remote result folder
                list_files_cmd = f"ls -1 {remote_result_path}"
                file_list_result = connection.run(
                    list_files_cmd, hide=True, warn=True
                )

                if file_list_result.exited != 0:
                    logger.warning(
                        f"Could not list files in {remote_result_path}"
                    )
                    all_success = False
                    continue

                files = file_list_result.stdout.strip().split("\n")
                files = [f.strip() for f in files if f.strip()]

                if not files:
                    logger.warning(f"No files found in {remote_result_path}")
                    continue

                logger.info(f"Found {len(files)} files to download for {app}")

                # Download each file
                for file in files:
                    remote_file_path = f"{remote_result_path}/{file}"
                    local_file_path = os.path.join(local_app_server_path, file)

                    try:
                        connection.get(remote_file_path, local_file_path)
                        logger.info(f"  Downloaded: {file}")
                    except Exception as e:
                        logger.error(f"  Failed to download {file}: {e}")
                        all_success = False

                logger.info(f"Completed processing {app}")

            except Exception as e:
                logger.error(f"Error processing application {app}: {e}")
                all_success = False

        if all_success:
            logger.info("Successfully retrieved all server results")
        else:
            logger.warning(
                "Some errors occurred while retrieving server results"
            )

        return all_success

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error retrieving server results: {e}")
        return False
    finally:
        if connection:
            try:
                connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def get_client_results(
    local_folder: str, method: str, hosts_config_file: str = "hosts_config.yaml"
) -> bool:
    """
    Pull client results from amari host for all applications.

    This function retrieves result files from the amari host for four applications:
    file-transfer, video-od, video-sr, and video-transcoding. Each application has
    a client folder with result/results subfolder containing output files.

    Local directory structure created:
        local_folder/
          ├── file-transfer/
          │   └── client/
          │       └── (result files)
          ├── video-od/
          │   └── client/
          │       └── (result files)
          ├── video-sr/
          │   └── client/
          │       └── (result files)
          └── video-transcoding/
              └── client/
                  └── (result files)

    Args:
        local_folder: Local folder path where results should be saved
        method: Method name (subfolder under apps_path)
        hosts_config_file: Path to the hosts configuration YAML file

    Returns:
        True if all files were successfully retrieved, False otherwise

    Example:
        >>> get_client_results("./results", "smec")
        True
    """
    logger = logging.getLogger(__name__)
    connection = None

    # Four applications to process
    applications = [
        "file-transfer",
        "video-od",
        "video-sr",
        "video-transcoding",
    ]

    try:
        # Load hosts configuration
        config = load_hosts_config(hosts_config_file)
        amari_config = config["hosts"]["amari"]

        # Get apps_path from configuration
        apps_path = amari_config["paths"]["apps_path"]

        # Create connection parameters
        connect_kwargs = {}
        if "key_filename" in amari_config:
            key_file = os.path.expanduser(amari_config["key_filename"])
            connect_kwargs["key_filename"] = [key_file]

        # Build connection config
        conn_config = {
            "host": amari_config["host"],
            "user": amari_config["user"],
            "port": amari_config.get("port", 22),
            "connect_kwargs": connect_kwargs,
        }

        # Handle proxy/gateway if specified
        if "proxy_command" in amari_config:
            # Extract proxy host from proxy_command
            # Format: "ssh user@proxy_host -W %h:%p"
            proxy_command = amari_config["proxy_command"]
            if "ssh" in proxy_command and "@" in proxy_command:
                # Parse proxy user and host
                parts = proxy_command.split()
                for part in parts:
                    if "@" in part:
                        proxy_user, proxy_host = part.split("@")
                        # Create gateway connection
                        gateway_kwargs = {}
                        if "key_filename" in amari_config:
                            key_file = os.path.expanduser(
                                amari_config["key_filename"]
                            )
                            gateway_kwargs["key_filename"] = [key_file]

                        gateway = Connection(
                            host=proxy_host,
                            user=proxy_user,
                            connect_kwargs=gateway_kwargs,
                        )
                        conn_config["gateway"] = gateway
                        break

        # Create connection
        connection = Connection(**conn_config)
        connection.open()

        logger.info(f"Connected to amari: {amari_config['host']}")

        # Create base local directory if it doesn't exist
        if not os.path.exists(local_folder):
            os.makedirs(local_folder, exist_ok=True)
            logger.info(f"Created local directory: {local_folder}")

        # Process each application
        all_success = True
        for app in applications:
            try:
                logger.info(f"Processing application: {app}")

                # Remote path for this application
                remote_app_path = f"{apps_path}/{method}/{app}/client"

                # Check if result or results folder exists
                check_result_cmd = (
                    f"[ -d '{remote_app_path}/result' ] && echo 'result' || (["
                    f" -d '{remote_app_path}/results' ] && echo 'results' ||"
                    " echo 'none')"
                )
                result_check = connection.run(
                    check_result_cmd, hide=True, warn=True
                )

                if result_check.exited != 0:
                    logger.warning(f"Could not check result folder for {app}")
                    all_success = False
                    continue

                result_folder_name = result_check.stdout.strip()

                if result_folder_name == "none":
                    logger.warning(
                        f"No result/results folder found for {app} at"
                        f" {remote_app_path}"
                    )
                    all_success = False
                    continue

                # Remote result path
                remote_result_path = f"{remote_app_path}/{result_folder_name}"
                logger.info(
                    f"Found {result_folder_name} folder at {remote_result_path}"
                )

                # Create local directory structure: local_folder/app/client/
                local_app_client_path = os.path.join(
                    local_folder, app, "client"
                )
                if not os.path.exists(local_app_client_path):
                    os.makedirs(local_app_client_path, exist_ok=True)
                    logger.info(
                        f"Created local directory: {local_app_client_path}"
                    )

                # Get list of files in remote result folder
                list_files_cmd = f"ls -1 {remote_result_path}"
                file_list_result = connection.run(
                    list_files_cmd, hide=True, warn=True
                )

                if file_list_result.exited != 0:
                    logger.warning(
                        f"Could not list files in {remote_result_path}"
                    )
                    all_success = False
                    continue

                files = file_list_result.stdout.strip().split("\n")
                files = [f.strip() for f in files if f.strip()]

                if not files:
                    logger.warning(f"No files found in {remote_result_path}")
                    continue

                logger.info(f"Found {len(files)} files to download for {app}")

                # Download each file
                for file in files:
                    remote_file_path = f"{remote_result_path}/{file}"
                    local_file_path = os.path.join(local_app_client_path, file)

                    try:
                        connection.get(remote_file_path, local_file_path)
                        logger.info(f"  Downloaded: {file}")
                    except Exception as e:
                        logger.error(f"  Failed to download {file}: {e}")
                        all_success = False

                logger.info(f"Completed processing {app}")

            except Exception as e:
                logger.error(f"Error processing application {app}: {e}")
                all_success = False

        if all_success:
            logger.info("Successfully retrieved all client results")
        else:
            logger.warning(
                "Some errors occurred while retrieving client results"
            )

        return all_success

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error retrieving client results: {e}")
        return False
    finally:
        if connection:
            try:
                connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")


def clean_results(hosts_config_file: str = "hosts_config.yaml") -> bool:
    """
    Clean client and server results by running result_cleaner.py on both hosts.

    This function connects to both amari and edge_server hosts and executes
    the result_cleaner.py script in their respective apps_path directories:
    - amari: /root/edge-applications/result_cleaner.py
    - edge_server: /home/zx/edge-applications/result_cleaner.py

    Args:
        hosts_config_file: Path to the hosts configuration YAML file

    Returns:
        True if both cleanup scripts executed successfully, False otherwise

    Example:
        >>> clean_results()
        True
    """
    logger = logging.getLogger(__name__)

    # Load hosts configuration
    try:
        config = load_hosts_config(hosts_config_file)
    except Exception as e:
        logger.error(f"Failed to load hosts configuration: {e}")
        return False

    all_success = True

    # Define hosts to clean: (host_key, description)
    hosts_to_clean = [
        ("amari", "amari (client)"),
        ("edge_server", "edge_server (server)"),
    ]

    for host_key, description in hosts_to_clean:
        connection = None
        try:
            logger.info(f"Cleaning results on {description}...")

            host_config = config["hosts"][host_key]
            apps_path = host_config["paths"]["apps_path"]
            cleaner_script = f"{apps_path}/result_cleaner.py"

            # Create connection parameters
            connect_kwargs = {}
            if "key_filename" in host_config:
                key_file = os.path.expanduser(host_config["key_filename"])
                connect_kwargs["key_filename"] = [key_file]

            # Build connection config
            conn_config = {
                "host": host_config["host"],
                "user": host_config["user"],
                "port": host_config.get("port", 22),
                "connect_kwargs": connect_kwargs,
            }

            # Handle proxy/gateway if specified
            if "proxy_command" in host_config:
                # Extract proxy host from proxy_command
                proxy_command = host_config["proxy_command"]
                if "ssh" in proxy_command and "@" in proxy_command:
                    # Parse proxy user and host
                    parts = proxy_command.split()
                    for part in parts:
                        if "@" in part:
                            proxy_user, proxy_host = part.split("@")
                            # Create gateway connection
                            gateway_kwargs = {}
                            if "key_filename" in host_config:
                                key_file = os.path.expanduser(
                                    host_config["key_filename"]
                                )
                                gateway_kwargs["key_filename"] = [key_file]

                            gateway = Connection(
                                host=proxy_host,
                                user=proxy_user,
                                connect_kwargs=gateway_kwargs,
                            )
                            conn_config["gateway"] = gateway
                            break

            # Create connection
            connection = Connection(**conn_config)
            connection.open()

            logger.info(f"Connected to {description}: {host_config['host']}")

            # Run the result_cleaner.py script
            clean_cmd = f"cd {apps_path} && python3 result_cleaner.py"
            logger.info(f"Executing: {clean_cmd}")

            result = connection.run(clean_cmd, hide=False, warn=True)

            if result.exited == 0:
                logger.info(f"Successfully cleaned results on {description}")
                logger.info(f"Output: {result.stdout.strip()}")
            else:
                logger.error(f"Failed to clean results on {description}")
                logger.error(
                    "Error:"
                    f" {result.stderr.strip() if result.stderr else 'Unknown error'}"
                )
                all_success = False

        except Exception as e:
            logger.error(f"Error cleaning results on {description}: {e}")
            all_success = False

        finally:
            if connection:
                try:
                    connection.close()
                    logger.info(f"Connection closed for {description}")
                except Exception as e:
                    logger.warning(
                        f"Error closing connection for {description}: {e}"
                    )

    if all_success:
        logger.info("Successfully cleaned results on all hosts")
    else:
        logger.warning("Some errors occurred while cleaning results")

    return all_success
