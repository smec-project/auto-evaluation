#!/usr/bin/env python3
"""
SMEC Environment Setup Script

- Restarts LTE service on amari host
- Starts 5G gNB on ran_server host (apps/gnb/gnb)
- Starts smec_controller on ran_server host (python3 main.py --log in conda smec env)
"""

import logging
import time
from typing import Dict, Any
from .host_manager import HostManager


class SMECEnvSetup:
    """SMEC environment setup for LTE, 5G, and SMEC controller testing."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        self.host_manager = HostManager(config_file)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def restart_lte_service(self) -> Dict[str, Any]:
        self.logger.info("Starting LTE service restart on amari...")
        try:
            result = self.host_manager.execute_on_host(
                host_name="amari",
                command="service lte restart",
                background=False,
            )
            if result["success"]:
                self.logger.info(
                    "LTE service restart command executed successfully"
                )
                self.logger.info(f"Exit code: {result.get('exit_code', 'N/A')}")
                if result.get("output"):
                    self.logger.info(f"Output: {result['output']}")
            else:
                self.logger.error(
                    f"Failed to restart LTE service: {result['error']}"
                )
            return result
        except Exception as e:
            self.logger.error(f"Exception during LTE service restart: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "amari",
            }

    def start_5g_gnb(self) -> Dict[str, Any]:
        self.logger.info("Starting 5G gNB on ran_server (apps/gnb/gnb)...")

        # Get srsRAN path from config
        ran_server_config = self.host_manager.config.get("hosts", {}).get(
            "ran_server", {}
        )
        srsran_path = ran_server_config.get("paths", {}).get(
            "srsRAN_path", "~/srsRAN_Project"
        )

        gnb_command = (
            f"cd {srsran_path}/build/ && sudo apps/gnb/gnb -c"
            " ../configs/gnb_rf_x310_tdd_n78_80mhz-63-samsung-smec.yml -c"
            " ../configs/qam256.yml ../configs/latency-control.yml"
        )
        try:
            result = self.host_manager.execute_on_host(
                host_name="ran_server",
                command=gnb_command,
                session_name="smec_gnb",
            )
            if result["success"]:
                self.logger.info("5G gNB started successfully (apps/gnb/gnb)")
                self.logger.info(f"Process PID: {result.get('pid', 'N/A')}")
            else:
                self.logger.error(f"Failed to start 5G gNB: {result['error']}")
            return result
        except Exception as e:
            self.logger.error(f"Exception during 5G gNB startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "ran_server",
            }

    def start_smec_controller(self) -> Dict[str, Any]:
        self.logger.info(
            "Starting SMEC controller on ran_server (conda env smec)..."
        )

        # Get srsRAN path from config
        ran_server_config = self.host_manager.config.get("hosts", {}).get(
            "ran_server", {}
        )
        srsran_path = ran_server_config.get("paths", {}).get(
            "srsRAN_path", "~/srsRAN_Project"
        )

        # Use full path to conda
        # smec_command = (
        #     f"cd {srsran_path}/smec_controller && "
        #     "~/miniconda3/bin/conda run -n smec python3 main.py --log"
        # )
        smec_command = (
            f"cd {srsran_path}/smec_controller && python3 main.py --log"
        )

        try:
            result = self.host_manager.execute_on_host(
                host_name="ran_server",
                command=smec_command,
                session_name="smec_controller",
            )
            if result["success"]:
                self.logger.info("SMEC controller started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
                if result.get("pid"):
                    self.logger.info(f"Process PID: {result['pid']}")
            else:
                self.logger.error(
                    f"Failed to start SMEC controller: {result['error']}"
                )
            return result
        except Exception as e:
            self.logger.error(f"Exception during SMEC controller startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "ran_server",
            }

    def setup_complete_environment(self, wait_time: int = 10) -> Dict[str, Any]:
        self.logger.info("Starting complete SMEC environment setup...")
        results = {
            "lte_restart": None,
            "5g_gnb_start": None,
            "smec_controller_start": None,
            "overall_success": False,
        }
        # Step 1: Restart LTE service
        self.logger.info("Step 1: Restarting LTE service on amari")
        results["lte_restart"] = self.restart_lte_service()
        if not results["lte_restart"]["success"]:
            self.logger.error("LTE service restart failed, stopping setup")
            return results
        self.logger.info(
            f"Waiting {wait_time} seconds for LTE service to stabilize..."
        )
        time.sleep(wait_time)
        # Step 2: Start 5G gNB
        self.logger.info("Step 2: Starting 5G gNB on ran_server (apps/gnb/gnb)")
        results["5g_gnb_start"] = self.start_5g_gnb()
        if not results["5g_gnb_start"]["success"]:
            self.logger.error("5G gNB startup failed")
            return results
        self.logger.info(f"Waiting 5 seconds for 5G gNB to initialize...")
        time.sleep(5)
        # Step 3: Start SMEC controller
        self.logger.info(
            "Step 3: Starting SMEC controller on ran_server (conda env smec)"
        )
        results["smec_controller_start"] = self.start_smec_controller()
        if not results["smec_controller_start"]["success"]:
            self.logger.error("SMEC controller startup failed")
            return results
        results["overall_success"] = (
            results["lte_restart"]["success"]
            and results["5g_gnb_start"]["success"]
            and results["smec_controller_start"]["success"]
        )
        if results["overall_success"]:
            self.logger.info("Complete SMEC environment setup successful!")
        else:
            self.logger.error("SMEC environment setup completed with errors")
        return results

    def cleanup_environment(self) -> Dict[str, Any]:
        self.logger.info("Starting SMEC environment cleanup...")
        results = {
            "lte_stop": None,
            "5g_gnb_stop": None,
            "smec_controller_stop": None,
            "overall_success": False,
        }
        # Stop SMEC controller
        self.logger.info("Stopping SMEC controller on ran_server...")
        try:
            stop_cmd = (
                "tmux kill-session -t smec_controller 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            results["smec_controller_stop"] = self.host_manager.execute_on_host(
                host_name="ran_server", command=stop_cmd, background=False
            )
            results["smec_controller_stop"]["success"] = True
            self.logger.info(
                "SMEC controller cleanup completed (tmux session killed)"
            )
        except Exception as e:
            self.logger.error(f"Exception during SMEC controller cleanup: {e}")
            results["smec_controller_stop"] = {
                "success": False,
                "error": str(e),
            }
        # Stop 5G gNB
        self.logger.info("Stopping 5G gNB on ran_server...")
        try:
            stop_cmd = (
                "tmux kill-session -t smec_gnb 2>/dev/null || true; "
                "sudo pkill -f 'gnb' 2>/dev/null || true"
            )
            results["5g_gnb_stop"] = self.host_manager.execute_on_host(
                host_name="ran_server", command=stop_cmd, background=False
            )
            results["5g_gnb_stop"]["success"] = True
            self.logger.info("5G gNB cleanup completed (tmux session killed)")
        except Exception as e:
            self.logger.error(f"Exception during 5G gNB cleanup: {e}")
            results["5g_gnb_stop"] = {"success": False, "error": str(e)}
        # Stop LTE service
        self.logger.info("Stopping LTE service on amari...")
        try:
            results["lte_stop"] = self.host_manager.execute_on_host(
                host_name="amari", command="service lte stop", background=False
            )
            if results["lte_stop"]["success"]:
                self.logger.info("LTE service stopped successfully")
            else:
                self.logger.warning("Failed to stop LTE service")
        except Exception as e:
            self.logger.error(f"Exception during LTE service cleanup: {e}")
            results["lte_stop"] = {"success": False, "error": str(e)}
        results["overall_success"] = (
            results["smec_controller_stop"]["success"]
            and results["5g_gnb_stop"]["success"]
            and results["lte_stop"]["success"]
        )
        if results["overall_success"]:
            self.logger.info("SMEC environment cleanup completed successfully!")
        else:
            self.logger.warning(
                "SMEC environment cleanup completed with some errors"
            )
        return results
