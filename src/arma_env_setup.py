#!/usr/bin/env python3
"""
ARMA Environment Setup Script

- Restarts LTE service on amari host
- Starts 5G gNB on edge0 host (apps/gnb/gnb)
- Starts arma_controller on edge0 host (python3 arma_controller.py in conda arma env)
"""

import logging
import time
from typing import Dict, Any
from .host_manager import HostManager


class ARMAEnvSetup:
    """ARMA environment setup for LTE, 5G, and ARMA controller testing."""

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
        self.logger.info("Starting 5G gNB on edge0 (apps/gnb/gnb)...")

        gnb_command = (
            "cd ~/srsRAN_Project/build/ && sudo apps/gnb/gnb -c"
            " ../configs/gnb_rf_x310_tdd_n78_80mhz-63-samsung-arma.yml -c"
            " ../configs/qam256.yml ../configs/latency-control.yml"
        )
        try:
            result = self.host_manager.execute_on_host(
                host_name="edge0", command=gnb_command, session_name="arma_gnb"
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
                "connection_info": "edge0",
            }

    def start_arma_controller(self) -> Dict[str, Any]:
        self.logger.info(
            "Starting ARMA controller on edge0 (conda env arma)..."
        )

        # Use full path to conda
        # arma_command = (
        #     "cd ~/srsRAN_Project/arma_controller && "
        #     "~/miniconda3/bin/conda run -n arma python3 arma_controller.py"
        # )
        arma_command = "cd ~/srsRAN_Project/arma_controller && python3 main.py"

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge0",
                command=arma_command,
                session_name="arma_controller",
            )
            if result["success"]:
                self.logger.info("ARMA controller started successfully")
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
                if result.get("pid"):
                    self.logger.info(f"Process PID: {result['pid']}")
            else:
                self.logger.error(
                    f"Failed to start ARMA controller: {result['error']}"
                )
            return result
        except Exception as e:
            self.logger.error(f"Exception during ARMA controller startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge0",
            }

    def setup_complete_environment(self, wait_time: int = 10) -> Dict[str, Any]:
        self.logger.info("Starting complete ARMA environment setup...")
        results = {
            "lte_restart": None,
            "5g_gnb_start": None,
            "arma_controller_start": None,
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
        self.logger.info("Step 2: Starting 5G gNB on edge0 (apps/gnb/gnb)")
        results["5g_gnb_start"] = self.start_5g_gnb()
        if not results["5g_gnb_start"]["success"]:
            self.logger.error("5G gNB startup failed")
            return results
        self.logger.info(f"Waiting 5 seconds for 5G gNB to initialize...")
        time.sleep(5)
        # Step 3: Start ARMA controller
        self.logger.info(
            "Step 3: Starting ARMA controller on edge0 (conda env arma)"
        )
        results["arma_controller_start"] = self.start_arma_controller()
        if not results["arma_controller_start"]["success"]:
            self.logger.error("ARMA controller startup failed")
            return results
        results["overall_success"] = (
            results["lte_restart"]["success"]
            and results["5g_gnb_start"]["success"]
            and results["arma_controller_start"]["success"]
        )
        if results["overall_success"]:
            self.logger.info("Complete ARMA environment setup successful!")
        else:
            self.logger.error("ARMA environment setup completed with errors")
        return results

    def cleanup_environment(self) -> Dict[str, Any]:
        self.logger.info("Starting ARMA environment cleanup...")
        results = {
            "lte_stop": None,
            "5g_gnb_stop": None,
            "arma_controller_stop": None,
            "overall_success": False,
        }
        # Stop ARMA controller
        self.logger.info("Stopping ARMA controller on edge0...")
        try:
            stop_cmd = (
                "tmux kill-session -t arma_controller 2>/dev/null || true; "
                "sudo pkill -f 'main.py' 2>/dev/null || true"
            )
            results["arma_controller_stop"] = self.host_manager.execute_on_host(
                host_name="edge0", command=stop_cmd, background=False
            )
            results["arma_controller_stop"]["success"] = True
            self.logger.info(
                "ARMA controller cleanup completed (tmux session killed)"
            )
        except Exception as e:
            self.logger.error(f"Exception during ARMA controller cleanup: {e}")
            results["arma_controller_stop"] = {
                "success": False,
                "error": str(e),
            }
        # Stop 5G gNB
        self.logger.info("Stopping 5G gNB on edge0...")
        try:
            stop_cmd = (
                "tmux kill-session -t arma_gnb 2>/dev/null || true; "
                "sudo pkill -f 'gnb' 2>/dev/null || true"
            )
            results["5g_gnb_stop"] = self.host_manager.execute_on_host(
                host_name="edge0", command=stop_cmd, background=False
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
            results["arma_controller_stop"]["success"]
            and results["5g_gnb_stop"]["success"]
            and results["lte_stop"]["success"]
        )
        if results["overall_success"]:
            self.logger.info("ARMA environment cleanup completed successfully!")
        else:
            self.logger.warning(
                "ARMA environment cleanup completed with some errors"
            )
        return results
