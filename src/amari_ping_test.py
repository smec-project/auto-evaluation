#!/usr/bin/env python3
"""
Amari Ping Test

This script runs ping tests from multiple UE network namespaces on amari host:
- Supports configurable number of UE namespaces (default: 8)
- Runs ping tests concurrently using multithreading
- Tests connectivity from each UE namespace to 192.168.2.3
- Waits for all ping tests to complete and reports health status
"""

import logging
import threading
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .host_manager import HostManager


class AmariPingTest:
    """Ping test executor for configurable number of UE network namespaces on amari."""

    def __init__(
        self, config_file: str = "hosts_config.yaml", num_ues: int = 8
    ):
        """
        Initialize the ping test executor.

        Args:
            config_file: Path to the host configuration file
            num_ues: Number of UE namespaces to test (default: 8)
        """
        self.host_manager = HostManager(config_file)
        self.num_ues = num_ues
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def ping_single_ue(self, ue_id: int) -> Dict[str, Any]:
        """
        Run ping test for a single UE namespace.

        Args:
            ue_id: UE ID (starting from 1)

        Returns:
            Dictionary containing ping test results
        """
        # Command: ip netns exec ue{N} ping 192.168.2.3 -c 10 -i 0.2
        ping_command = f"ip netns exec ue{ue_id} ping 192.168.2.3 -c 10 -i 0.2"

        try:
            result = self.host_manager.execute_on_host(
                host_name="amari", command=ping_command, background=False
            )

            # Parse ping statistics
            ping_stats = self._parse_ping_output(result.get("output", ""))

            # Determine success based on exit code and packet loss
            success = (
                result["success"] and ping_stats["packet_loss_percent"] < 100
            )

            ping_result = {
                "ue_id": ue_id,
                "success": success,
                "exit_code": result.get("exit_code", -1),
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "stats": ping_stats,
            }

            # Only log details if not in quiet mode (controlled by caller)
            # Detailed logging is handled by the caller if needed

            return ping_result

        except Exception as e:
            self.logger.error(f"Exception during UE{ue_id} ping test: {e}")
            return {
                "ue_id": ue_id,
                "success": False,
                "exit_code": -1,
                "output": "",
                "error": str(e),
                "stats": {
                    "packets_sent": 0,
                    "packets_received": 0,
                    "packet_loss_percent": 100,
                    "min_rtt": 0,
                    "avg_rtt": 0,
                    "max_rtt": 0,
                },
            }

    def _parse_ping_output(self, output: str) -> Dict[str, float]:
        """
        Parse ping command output to extract statistics.

        Args:
            output: Raw ping command output

        Returns:
            Dictionary containing parsed ping statistics
        """
        stats = {
            "packets_sent": 0,
            "packets_received": 0,
            "packet_loss_percent": 100,
            "min_rtt": 0,
            "avg_rtt": 0,
            "max_rtt": 0,
        }

        try:
            lines = output.split("\n")

            # Parse packet statistics line
            # Example: "10 packets transmitted, 8 received, 20% packet loss, time 9010ms"
            for line in lines:
                if "packets transmitted" in line and "received" in line:
                    parts = line.split(",")
                    if len(parts) >= 3:
                        # Extract transmitted packets
                        transmitted_part = parts[0].strip()
                        if "packets transmitted" in transmitted_part:
                            stats["packets_sent"] = int(
                                transmitted_part.split()[0]
                            )

                        # Extract received packets
                        received_part = parts[1].strip()
                        if "received" in received_part:
                            stats["packets_received"] = int(
                                received_part.split()[0]
                            )

                        # Extract packet loss percentage
                        loss_part = parts[2].strip()
                        if "% packet loss" in loss_part:
                            loss_str = loss_part.split("%")[0].strip()
                            stats["packet_loss_percent"] = float(loss_str)
                    break

            # Parse RTT statistics line
            # Example: "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms"
            for line in lines:
                if "rtt min/avg/max" in line and "=" in line:
                    rtt_part = line.split("=")[1].strip()
                    if "ms" in rtt_part:
                        rtt_values = (
                            rtt_part.replace("ms", "").strip().split("/")
                        )
                        if len(rtt_values) >= 3:
                            stats["min_rtt"] = float(rtt_values[0])
                            stats["avg_rtt"] = float(rtt_values[1])
                            stats["max_rtt"] = float(rtt_values[2])
                    break

        except (ValueError, IndexError) as e:
            self.logger.warning(f"Failed to parse ping output: {e}")

        return stats

    def run_all_ping_tests(
        self, max_workers: int = None, quiet: bool = False
    ) -> Dict[str, Any]:
        """
        Run ping tests for all UE namespaces concurrently.

        Args:
            max_workers: Maximum number of concurrent threads (default: same as num_ues)
            quiet: If True, only log summary without detailed per-UE logs

        Returns:
            Dictionary containing results for all ping tests
        """

        if max_workers is None:
            max_workers = self.num_ues
        if not quiet:
            self.logger.info("=" * 60)
            self.logger.info("STARTING AMARI UE PING TESTS")
            self.logger.info("=" * 60)

        start_time = time.time()
        results = {}

        # Run ping tests concurrently for all configured UEs
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ping test tasks
            future_to_ue = {
                executor.submit(self.ping_single_ue, ue_id): ue_id
                for ue_id in range(1, self.num_ues + 1)
            }

            # Collect results as they complete
            for future in as_completed(future_to_ue):
                ue_id = future_to_ue[future]
                try:
                    result = future.result()
                    results[f"ue{ue_id}"] = result
                except Exception as e:
                    self.logger.error(
                        f"UE{ue_id} ping test generated an exception: {e}"
                    )
                    results[f"ue{ue_id}"] = {
                        "ue_id": ue_id,
                        "success": False,
                        "exit_code": -1,
                        "output": "",
                        "error": str(e),
                        "stats": {
                            "packets_sent": 0,
                            "packets_received": 0,
                            "packet_loss_percent": 100,
                            "min_rtt": 0,
                            "avg_rtt": 0,
                            "max_rtt": 0,
                        },
                    }

        end_time = time.time()
        duration = end_time - start_time

        # Analyze overall health
        health_report = self._analyze_health(results)

        # Add timing and summary info
        health_report["duration"] = duration
        health_report["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Log summary only if not quiet
        if not quiet:
            self._log_summary(health_report)

        return {"individual_results": results, "health_report": health_report}

    def _analyze_health(
        self, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze the health status of all ping tests.

        Args:
            results: Dictionary containing individual ping test results

        Returns:
            Dictionary containing health analysis
        """
        total_ues = len(results)
        successful_ues = sum(
            1 for result in results.values() if result["success"]
        )
        failed_ues = total_ues - successful_ues

        # Calculate aggregate statistics
        total_packets_sent = sum(
            result["stats"]["packets_sent"] for result in results.values()
        )
        total_packets_received = sum(
            result["stats"]["packets_received"] for result in results.values()
        )
        overall_loss_percent = (
            (
                (total_packets_sent - total_packets_received)
                / total_packets_sent
                * 100
            )
            if total_packets_sent > 0
            else 100
        )

        # Calculate average RTT for successful tests
        successful_rtts = [
            result["stats"]["avg_rtt"]
            for result in results.values()
            if result["success"] and result["stats"]["avg_rtt"] > 0
        ]
        avg_rtt = (
            sum(successful_rtts) / len(successful_rtts)
            if successful_rtts
            else 0
        )

        # Determine overall health status
        if successful_ues == total_ues:
            health_status = "EXCELLENT"
        elif successful_ues >= total_ues * 0.8:
            health_status = "GOOD"
        elif successful_ues >= total_ues * 0.5:
            health_status = "FAIR"
        else:
            health_status = "POOR"

        return {
            "health_status": health_status,
            "total_ues": total_ues,
            "successful_ues": successful_ues,
            "failed_ues": failed_ues,
            "success_rate_percent": (
                (successful_ues / total_ues * 100) if total_ues > 0 else 0
            ),
            "total_packets_sent": total_packets_sent,
            "total_packets_received": total_packets_received,
            "overall_packet_loss_percent": overall_loss_percent,
            "average_rtt_ms": avg_rtt,
            "failed_ue_list": [
                f"ue{result['ue_id']}"
                for result in results.values()
                if not result["success"]
            ],
        }

    def _log_summary(self, health_report: Dict[str, Any]):
        """
        Log a comprehensive summary of the ping test results.

        Args:
            health_report: Health analysis report
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("AMARI UE PING TEST SUMMARY")
        self.logger.info("=" * 60)

        # Health status
        status_symbol = {
            "EXCELLENT": "🟢",
            "GOOD": "🟡",
            "FAIR": "🟠",
            "POOR": "🔴",
        }.get(health_report["health_status"], "❓")

        self.logger.info(
            f"Overall Health: {status_symbol} {health_report['health_status']}"
        )
        self.logger.info(
            f"Test Duration: {health_report['duration']:.2f} seconds"
        )

        # UE status
        self.logger.info(
            "UE Status:"
            f" {health_report['successful_ues']}/{health_report['total_ues']} successful"
            f" ({health_report['success_rate_percent']:.1f}%)"
        )

        if health_report["failed_ue_list"]:
            self.logger.info(
                f"Failed UEs: {', '.join(health_report['failed_ue_list'])}"
            )

        # Overall packet loss
        self.logger.info(
            "Overall Packet Loss:"
            f" {health_report['overall_packet_loss_percent']:.1f}%"
        )

        # Performance metrics
        if health_report["average_rtt_ms"] > 0:
            self.logger.info(
                f"Average RTT: {health_report['average_rtt_ms']:.2f} ms"
            )

        self.logger.info("=" * 60)

    def quick_health_check(self) -> bool:
        """
        Run a quick ping test and return True if network is healthy.

        Returns:
            True if network connectivity is good (EXCELLENT or GOOD), False otherwise
        """
        self.logger.info("Running network connectivity check...")

        try:
            results = self.run_all_ping_tests(quiet=True)
            health_status = results["health_report"]["health_status"]
            success_rate = results["health_report"]["success_rate_percent"]

            if health_status in ["EXCELLENT", "GOOD"]:
                self.logger.info(
                    f"✓ Network connectivity check passed: {health_status} "
                    f"({success_rate:.1f}% UEs connected)"
                )
                return True
            else:
                self.logger.error(
                    f"✗ Network connectivity check failed: {health_status} "
                    f"({success_rate:.1f}% UEs connected)"
                )
                if results["health_report"]["failed_ue_list"]:
                    self.logger.error(
                        "Failed UEs:"
                        f" {', '.join(results['health_report']['failed_ue_list'])}"
                    )
                return False

        except Exception as e:
            self.logger.error(
                f"Network connectivity check failed with exception: {e}"
            )
            return False
